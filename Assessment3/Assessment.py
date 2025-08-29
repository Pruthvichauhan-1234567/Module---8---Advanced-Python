#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LibraDesk — a compact Tkinter + SQLite desktop app
Demonstrates:
- File I/O (save invoices as .txt/.csv)
- Exception handling (try/except/finally, custom exceptions)
- OOP with inheritance, overriding, and "overloading"-style defaults
- SQLite3 persistence
- Regex validation & search
- Tkinter GUI (forms, buttons, tables)
Role-based access:
- admin / admin123  -> full access
- librarian / lib123 -> limited (no add/edit books)
"""

import os
import re
import csv
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

APP_DIR = Path.home() / ".libradesk_demo"
DB_PATH = APP_DIR / "libradesk.sqlite3"
INVOICE_DIR = APP_DIR / "invoices"
APP_DIR.mkdir(parents=True, exist_ok=True)
INVOICE_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Custom Exceptions ----------
class ValidationError(Exception):
    """Raised when input validation fails."""

class PermissionError(Exception):
    """Raised when a user attempts an action without permission."""

# ---------- Data classes (OOP) ----------
@dataclass
class Person:
    name: str
    email: str

    def contact(self) -> str:
        return f"{self.name} <{self.email}>"

@dataclass
class Member(Person):
    member_id: int = field(default=None)

    # Override: provide more specific contact label
    def contact(self) -> str:  # overriding base method
        return f"Member #{self.member_id}: {super().contact()}"

@dataclass
class Book:
    title: str
    author: str
    genre: str
    isbn: str
    available: int = 1
    book_id: int = field(default=None)

    # "Overloading" style via default params (Pythonic)
    def label(self, include_isbn: bool = True):  # single method, optional arg
        s = f"{self.title} by {self.author}"
        return f"{s} (ISBN: {self.isbn})" if include_isbn else s

# ---------- Database Layer ----------
class LibraryDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS members(
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS books(
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                genre TEXT NOT NULL,
                isbn TEXT NOT NULL UNIQUE,
                available INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS transactions(
                tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                borrow_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                return_date TEXT,
                fine INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(member_id) REFERENCES members(member_id),
                FOREIGN KEY(book_id) REFERENCES books(book_id)
            );
            """
        )
        self.conn.commit()

    # ------------- Members -------------
    def add_member(self, m: Member) -> int:
        self._validate_email(m.email)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO members(name,email) VALUES(?,?)",
                (m.name, m.email),
            )
            return cur.lastrowid

    def update_member(self, member_id: int, name: str, email: str):
        self._validate_email(email)
        with self.conn:
            self.conn.execute(
                "UPDATE members SET name=?, email=? WHERE member_id=?",
                (name, email, member_id),
            )

    def list_members(self, pattern: str = ""):
        # regex search in Python after fetching (simple demo)
        rows = self.conn.execute("SELECT * FROM members").fetchall()
        if not pattern:
            return rows
        rgx = re.compile(pattern, re.IGNORECASE)
        return [r for r in rows if rgx.search(r["name"]) or rgx.search(r["email"])]

    # ------------- Books -------------
    def add_book(self, b: Book) -> int:
        self._validate_isbn(b.isbn)
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO books(title,author,genre,isbn,available) VALUES(?,?,?,?,?)",
                (b.title, b.author, b.genre, b.isbn, b.available),
            )
            return cur.lastrowid

    def update_book(self, book_id: int, title: str, author: str, genre: str, isbn: str, available: int):
        self._validate_isbn(isbn)
        with self.conn:
            self.conn.execute(
                "UPDATE books SET title=?,author=?,genre=?,isbn=?,available=? WHERE book_id=?",
                (title, author, genre, isbn, available, book_id),
            )

    def list_books(self, pattern: str = ""):
        rows = self.conn.execute("SELECT * FROM books").fetchall()
        if not pattern:
            return rows
        rgx = re.compile(pattern, re.IGNORECASE)
        out = []
        for r in rows:
            if any(rgx.search(str(r[k])) for k in ("title","author","genre","isbn")):
                out.append(r)
        return out

    # ------------- Borrow/Return -------------
    def borrow_book(self, member_id: int, book_id: int, days: int = 7):
        # use try/except for errors
        try:
            with self.conn:
                book = self.conn.execute("SELECT available FROM books WHERE book_id=?", (book_id,)).fetchone()
                if not book or book["available"] <= 0:
                    raise ValidationError("Book not available")
                self.conn.execute("UPDATE books SET available=available-1 WHERE book_id=?", (book_id,))
                now = datetime.now()
                due = now + timedelta(days=days)
                self.conn.execute(
                    "INSERT INTO transactions(member_id,book_id,borrow_date,due_date) VALUES(?,?,?,?)",
                    (member_id, book_id, now.isoformat(), due.date().isoformat()),
                )
        except sqlite3.Error as e:
            raise ValidationError(f"DB error: {e}")

    def return_book(self, tx_id: int, fine_per_day: int = 5):
        try:
            with self.conn:
                tx = self.conn.execute("SELECT * FROM transactions WHERE tx_id=?", (tx_id,)).fetchone()
                if not tx or tx["return_date"]:
                    raise ValidationError("Invalid transaction or already returned")
                due = datetime.fromisoformat(tx["due_date"] + "T00:00:00")
                today = datetime.now()
                overdue_days = max((today - due).days, 0)
                fine = overdue_days * fine_per_day
                self.conn.execute("UPDATE transactions SET return_date=?, fine=? WHERE tx_id=?",
                                  (today.date().isoformat(), fine, tx_id))
                self.conn.execute("UPDATE books SET available=available+1 WHERE book_id=?", (tx["book_id"],))
                return fine
        except sqlite3.Error as e:
            raise ValidationError(f"DB error: {e}")

    def active_loans(self):
        return self.conn.execute(
            "SELECT t.*, m.name as member_name, b.title as book_title FROM transactions t "
            "JOIN members m ON m.member_id=t.member_id "
            "JOIN books b ON b.book_id=t.book_id "
            "WHERE t.return_date IS NULL ORDER BY t.tx_id DESC"
        ).fetchall()

    def history(self):
        return self.conn.execute(
            "SELECT t.*, m.name as member_name, b.title as book_title FROM transactions t "
            "JOIN members m ON m.member_id=t.member_id "
            "JOIN books b ON b.book_id=t.book_id ORDER BY t.tx_id DESC"
        ).fetchall()

    # ------------- Validators -------------
    @staticmethod
    def _validate_email(email: str):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValidationError("Invalid email format")

    @staticmethod
    def _validate_isbn(isbn: str):
        # Simple regex: 10 or 13 digits, optionally with dashes
        if not re.match(r"^(97(8|9))?\d{9}(\d|X)$|^\d{1,5}-\d{1,7}-\d{1,7}-[\dX]$", isbn):
            raise ValidationError("Invalid ISBN")

# ---------- Invoice Generator (File I/O) ----------
class InvoiceGenerator:
    TAX_RATE = 0.0  # demo: zero tax; change if needed

    def __init__(self, out_dir=INVOICE_DIR):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # "overloaded" feel via optional args
    def write_invoice(self, tx_row, as_csv: bool = False):
        member = tx_row["member_name"]
        book = tx_row["book_title"]
        fine = tx_row["fine"]
        subtotal = fine
        tax = round(subtotal * self.TAX_RATE, 2)
        total = subtotal + tax
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"invoice_tx{tx_row['tx_id']}_{stamp}"

        if as_csv:
            path = self.out_dir / f"{base}.csv"
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["TX_ID","Member","Book","Fine","Tax","Total"])
                w.writerow([tx_row["tx_id"], member, book, fine, tax, total])
        else:
            path = self.out_dir / f"{base}.txt"
            with open(path, "w", encoding="utf-8") as f:
                f.write("LibraDesk Invoice\n")
                f.write(f"Transaction: {tx_row['tx_id']}\n")
                f.write(f"Member: {member}\n")
                f.write(f"Book: {book}\n")
                f.write(f"Fine: ₹{fine}\n")
                f.write(f"Tax: ₹{tax}\n")
                f.write(f"Total: ₹{total}\n")
        return path

# ---------- Auth ----------
USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "librarian": {"password": "lib123", "role": "librarian"},
}

# ---------- GUI ----------
class LibraDeskApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LibraDesk — Digital Library Manager")
        self.geometry("1050x650")
        self.db = LibraryDB()
        self.invoice_gen = InvoiceGenerator()
        self.user = None
        self._render_login()

    # ---------- Login ----------
    def _render_login(self):
        self.login_frame = ttk.Frame(self)
        self.login_frame.pack(expand=True)
        ttk.Label(self.login_frame, text="LibraDesk Login", font=("Segoe UI", 16, "bold")).grid(column=0, row=0, columnspan=2, pady=10)
        ttk.Label(self.login_frame, text="Username").grid(column=0, row=1, sticky="e", padx=5, pady=5)
        ttk.Label(self.login_frame, text="Password").grid(column=0, row=2, sticky="e", padx=5, pady=5)
        self.u_var, self.p_var = tk.StringVar(), tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.u_var).grid(column=1, row=1, padx=5, pady=5)
        ttk.Entry(self.login_frame, textvariable=self.p_var, show="*").grid(column=1, row=2, padx=5, pady=5)
        ttk.Button(self.login_frame, text="Login", command=self._do_login).grid(column=0, row=3, columnspan=2, pady=10)

    def _do_login(self):
        u, p = self.u_var.get().strip(), self.p_var.get().strip()
        record = USERS.get(u)
        if record and record["password"] == p:
            self.user = {"username": u, "role": record["role"]}
            self.login_frame.destroy()
            self._render_main()
        else:
            messagebox.showerror("Login failed", "Invalid username or password")

    # ---------- Main UI ----------
    def _render_main(self):
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text=f"Logged in as: {self.user['username']} ({self.user['role']})",
                  font=("Segoe UI", 11, "bold")).pack(side="left", padx=10, pady=8)
        ttk.Button(top, text="Logout", command=self._logout).pack(side="right", padx=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.members_tab = ttk.Frame(self.notebook)
        self.books_tab = ttk.Frame(self.notebook)
        self.borrow_tab = ttk.Frame(self.notebook)
        self.search_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.members_tab, text="Members")
        self.notebook.add(self.books_tab, text="Books")
        self.notebook.add(self.borrow_tab, text="Borrow/Return")
        self.notebook.add(self.search_tab, text="Search & Reports")

        self._build_members_tab()
        self._build_books_tab()
        self._build_borrow_tab()
        self._build_search_tab()

        if self.user["role"] == "librarian":
            for w in self.books_tab.winfo_children():
                try:
                    w.configure(state="disabled")
                except tk.TclError:
                    pass

    def _logout(self):
        self.notebook.destroy()
        for child in self.winfo_children():
            child.destroy()
        self.user = None
        self._render_login()

    # ---------- Members UI ----------
    def _build_members_tab(self):
        frm = self.members_tab
        # form
        form = ttk.LabelFrame(frm, text="Add / Update Member")
        form.pack(fill="x", padx=10, pady=10)
        self.m_name, self.m_email = tk.StringVar(), tk.StringVar()
        self.m_id = tk.StringVar()
        ttk.Label(form, text="Member ID (for update)").grid(column=0, row=0, padx=5, pady=5, sticky="e")
        ttk.Entry(form, textvariable=self.m_id, width=10).grid(column=1, row=0, padx=5, pady=5, sticky="w")
        ttk.Label(form, text="Name").grid(column=0, row=1, padx=5, pady=5, sticky="e")
        ttk.Entry(form, textvariable=self.m_name, width=30).grid(column=1, row=1, padx=5, pady=5, sticky="w")
        ttk.Label(form, text="Email").grid(column=0, row=2, padx=5, pady=5, sticky="e")
        ttk.Entry(form, textvariable=self.m_email, width=30).grid(column=1, row=2, padx=5, pady=5, sticky="w")
        ttk.Button(form, text="Add Member", command=self._add_member).grid(column=0, row=3, padx=5, pady=5)
        ttk.Button(form, text="Update Member", command=self._update_member).grid(column=1, row=3, padx=5, pady=5, sticky="w")

        # table
        table_frm = ttk.LabelFrame(frm, text="Members")
        table_frm.pack(fill="both", expand=True, padx=10, pady=10)
        self.members_tree = ttk.Treeview(table_frm, columns=("id","name","email"), show="headings")
        for i, h in enumerate(("ID","Name","Email")):
            self.members_tree.heading(i if i else "id", text=h)
        self.members_tree.heading("id", text="ID")
        self.members_tree.heading("name", text="Name")
        self.members_tree.heading("email", text="Email")
        self.members_tree.pack(fill="both", expand=True)
        self._refresh_members()

    def _add_member(self):
        try:
            member = Member(name=self.m_name.get().strip(), email=self.m_email.get().strip())
            new_id = self.db.add_member(member)
            messagebox.showinfo("Success", f"Member added with ID {new_id}")
            self._refresh_members()
        except ValidationError as e:
            messagebox.showerror("Validation", str(e))

    def _update_member(self):
        try:
            mid = int(self.m_id.get())
            self.db.update_member(mid, self.m_name.get().strip(), self.m_email.get().strip())
            messagebox.showinfo("Updated", "Member updated")
            self._refresh_members()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid Member ID")
        except ValidationError as e:
            messagebox.showerror("Validation", str(e))

    def _refresh_members(self):
        for r in self.members_tree.get_children():
            self.members_tree.delete(r)
        for row in self.db.list_members():
            self.members_tree.insert("", "end", values=(row["member_id"], row["name"], row["email"]))

    # ---------- Books UI ----------
    def _build_books_tab(self):
        frm = self.books_tab
        form = ttk.LabelFrame(frm, text="Add / Update Book")
        form.pack(fill="x", padx=10, pady=10)
        self.b_id = tk.StringVar()
        self.b_title, self.b_author, self.b_genre, self.b_isbn = map(tk.StringVar, range(4))
        self.b_avail = tk.IntVar(value=1)
        labels = ["Book ID (for update)", "Title", "Author", "Genre", "ISBN", "Available"]
        entries = [
            ttk.Entry(form, textvariable=self.b_id, width=10),
            ttk.Entry(form, textvariable=self.b_title, width=30),
            ttk.Entry(form, textvariable=self.b_author, width=30),
            ttk.Entry(form, textvariable=self.b_genre, width=30),
            ttk.Entry(form, textvariable=self.b_isbn, width=20),
            ttk.Entry(form, textvariable=self.b_avail, width=10),
        ]
        for i, (lab, ent) in enumerate(zip(labels, entries)):
            ttk.Label(form, text=lab).grid(column=0, row=i, padx=5, pady=4, sticky="e")
            ent.grid(column=1, row=i, padx=5, pady=4, sticky="w")
        ttk.Button(form, text="Add Book", command=self._add_book).grid(column=0, row=len(labels), padx=5, pady=5)
        ttk.Button(form, text="Update Book", command=self._update_book).grid(column=1, row=len(labels), padx=5, pady=5, sticky="w")

        table_frm = ttk.LabelFrame(frm, text="Books")
        table_frm.pack(fill="both", expand=True, padx=10, pady=10)
        self.books_tree = ttk.Treeview(table_frm, columns=("id","title","author","genre","isbn","avail"), show="headings")
        for col, head in zip(("id","title","author","genre","isbn","avail"), ("ID","Title","Author","Genre","ISBN","Available")):
            self.books_tree.heading(col, text=head)
        self.books_tree.pack(fill="both", expand=True)
        self._refresh_books()

    def _add_book(self):
        try:
            b = Book(
                title=self.b_title.get().strip(),
                author=self.b_author.get().strip(),
                genre=self.b_genre.get().strip(),
                isbn=self.b_isbn.get().strip(),
                available=int(self.b_avail.get() or 1),
            )
            bid = self.db.add_book(b)
            messagebox.showinfo("Success", f"Book added with ID {bid}")
            self._refresh_books()
        except ValidationError as e:
            messagebox.showerror("Validation", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update_book(self):
        try:
            bid = int(self.b_id.get())
            self.db.update_book(bid, self.b_title.get().strip(), self.b_author.get().strip(),
                                self.b_genre.get().strip(), self.b_isbn.get().strip(), int(self.b_avail.get()))
            messagebox.showinfo("Updated", "Book updated")
            self._refresh_books()
        except ValueError:
            messagebox.showerror("Error", "Enter a valid Book ID")
        except ValidationError as e:
            messagebox.showerror("Validation", str(e))

    def _refresh_books(self):
        for r in self.books_tree.get_children():
            self.books_tree.delete(r)
        for row in self.db.list_books():
            self.books_tree.insert("", "end", values=(row["book_id"], row["title"], row["author"], row["genre"], row["isbn"], row["available"]))

    # ---------- Borrow/Return UI ----------
    def _build_borrow_tab(self):
        frm = self.borrow_tab
        # Borrow
        l1 = ttk.LabelFrame(frm, text="Borrow Book")
        l1.pack(fill="x", padx=10, pady=10)
        self.br_member = tk.StringVar()
        self.br_book = tk.StringVar()
        self.br_days = tk.IntVar(value=7)
        for i, (lab, var) in enumerate([("Member ID", self.br_member), ("Book ID", self.br_book), ("Days", self.br_days)]):
            ttk.Label(l1, text=lab).grid(column=0, row=i, padx=5, pady=5, sticky="e")
            ttk.Entry(l1, textvariable=var, width=12).grid(column=1, row=i, padx=5, pady=5, sticky="w")
        ttk.Button(l1, text="Borrow", command=self._borrow).grid(column=0, row=3, columnspan=2, pady=6)

        # Active loans table
        l2 = ttk.LabelFrame(frm, text="Active Loans / Return")
        l2.pack(fill="both", expand=True, padx=10, pady=10)
        self.tx_tree = ttk.Treeview(l2, columns=("tx","member","book","borrowed","due"), show="headings")
        for col, head in zip(("tx","member","book","borrowed","due"), ("TX ID","Member","Book","Borrowed","Due")):
            self.tx_tree.heading(col, text=head)
        self.tx_tree.pack(fill="both", expand=True)

        ret_frm = ttk.Frame(l2)
        ret_frm.pack(fill="x", pady=6)
        ttk.Label(ret_frm, text="TX ID").pack(side="left", padx=4)
        self.ret_tx = tk.StringVar()
        ttk.Entry(ret_frm, textvariable=self.ret_tx, width=10).pack(side="left")
        ttk.Button(ret_frm, text="Return & Generate Invoice (.txt)", command=self._return_txt).pack(side="left", padx=6)
        ttk.Button(ret_frm, text="Return & Generate Invoice (.csv)", command=self._return_csv).pack(side="left")
        self._refresh_loans()

    def _borrow(self):
        try:
            self.db.borrow_book(int(self.br_member.get()), int(self.br_book.get()), int(self.br_days.get()))
            messagebox.showinfo("Borrowed", "Book checked out")
            self._refresh_loans()
            self._refresh_books()
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Error", str(e))

    def _return_common(self, as_csv=False):
        try:
            fine = self.db.return_book(int(self.ret_tx.get()))
            self._refresh_loans()
            self._refresh_books()
            # find row to make invoice
            for row in self.db.history():
                if row["tx_id"] == int(self.ret_tx.get()):
                    path = self.invoice_gen.write_invoice(row, as_csv=as_csv)
                    messagebox.showinfo("Returned", f"Fine: ₹{fine}\nInvoice saved:\n{path}")
                    return
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Error", str(e))

    def _return_txt(self):
        self._return_common(as_csv=False)

    def _return_csv(self):
        self._return_common(as_csv=True)

    def _refresh_loans(self):
        for r in self.tx_tree.get_children():
            self.tx_tree.delete(r)
        for row in self.db.active_loans():
            self.tx_tree.insert("", "end", values=(row["tx_id"], row["member_name"], row["book_title"], row["borrow_date"][:10], row["due_date"]))

    # ---------- Search & Reports ----------
    def _build_search_tab(self):
        frm = self.search_tab
        bar = ttk.Frame(frm)
        bar.pack(fill="x", padx=10, pady=10)
        ttk.Label(bar, text="Regex pattern").pack(side="left")
        self.search_pattern = tk.StringVar()
        ttk.Entry(bar, textvariable=self.search_pattern, width=40).pack(side="left", padx=6)
        ttk.Button(bar, text="Search Books", command=self._search_books).pack(side="left")
        ttk.Button(bar, text="Overdue List", command=self._overdue_list).pack(side="left", padx=6)

        self.search_tree = ttk.Treeview(frm, columns=("kind","c1","c2","c3"), show="headings")
        for col, head in zip(("kind","c1","c2","c3"), ("Type","Col1","Col2","Col3")):
            self.search_tree.heading(col, text=head)
        self.search_tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _search_books(self):
        pat = self.search_pattern.get().strip()
        rows = self.db.list_books(pattern=pat)
        self._fill_search([("Book", r["title"], r["author"], r["isbn"]) for r in rows])

    def _overdue_list(self):
        out = []
        today = datetime.now().date()
        for r in self.db.active_loans():
            due = datetime.fromisoformat(r["due_date"]).date()
            if due < today:
                out.append(("Overdue", r["member_name"], r["book_title"], str((today - due).days)+" days"))
        self._fill_search(out)

    def _fill_search(self, rows):
        for r in self.search_tree.get_children():
            self.search_tree.delete(r)
        for row in rows:
            self.search_tree.insert("", "end", values=row)

# ---------- Seed data on first run ----------
def seed_if_empty(db: LibraryDB):
    if not db.list_members():
        db.add_member(Member(name="Alice Sharma", email="alice@example.com"))
        db.add_member(Member(name="Bob Khan", email="bob@example.com"))
    if not db.list_books():
        db.add_book(Book(title="Python Crash Course", author="Eric Matthes", genre="Programming", isbn="9781593276034", available=3))
        db.add_book(Book(title="Clean Code", author="Robert C. Martin", genre="Software", isbn="9780132350884", available=2))
        db.add_book(Book(title="Atomic Habits", author="James Clear", genre="Self-help", isbn="9780735211292", available=5))

if __name__ == "__main__":
    app = LibraDeskApp()
    seed_if_empty(app.db)
    app.mainloop()
# 9. Write Python programs to demonstrate different types of inheritance (single, multiple, multilevel, etc.).

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, re

# ---------- Database Setup ----------
con = sqlite3.connect("meditrack.db")
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, age INT, disease TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS appointments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INT, doctor TEXT, date TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS billing(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INT, amount REAL, details TEXT
)""")
con.commit()

# ---------- Main App ----------
class MediTrack:
    def _init_(self, root):
        self.root = root
        self.root.title("MediTrack - Healthcare Management System")
        self.root.geometry("1000x650")

        # Tabbed Interface
        tabControl = ttk.Notebook(root)
        self.tab1 = ttk.Frame(tabControl)
        self.tab2 = ttk.Frame(tabControl)
        self.tab3 = ttk.Frame(tabControl)
        self.tab4 = ttk.Frame(tabControl)
        self.tab5 = ttk.Frame(tabControl)

        tabControl.add(self.tab1, text="Patient Management")
        tabControl.add(self.tab2, text="Appointments")
        tabControl.add(self.tab3, text="Billing")
        tabControl.add(self.tab4, text="Reports/Search")
        tabControl.add(self.tab5, text="User Login")
        tabControl.pack(expand=1, fill="both")

        self.patient_tab()
        self.appointment_tab()
        self.billing_tab()
        self.search_tab()
        self.login_tab()

    # ---------- Patient Management ----------
    def patient_tab(self):
        frame = tk.Frame(self.tab1, padx=20, pady=20)
        frame.pack(fill="both")

        tk.Label(frame, text="Patient Name").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(frame, text="Age").grid(row=1, column=0, padx=10, pady=5)
        tk.Label(frame, text="Disease").grid(row=2, column=0, padx=10, pady=5)

        self.pname = tk.Entry(frame); self.pname.grid(row=0, column=1)
        self.page = tk.Entry(frame); self.page.grid(row=1, column=1)
        self.pdisease = tk.Entry(frame); self.pdisease.grid(row=2, column=1)

        tk.Button(frame, text="Add Patient", command=self.add_patient, bg="lightblue").grid(row=3, column=0, pady=10)
        tk.Button(frame, text="View Patients", command=self.view_patients, bg="lightgreen").grid(row=3, column=1, pady=10)

        # Treeview for Patients
        self.patient_tree = ttk.Treeview(frame, columns=("ID","Name","Age","Disease"), show="headings", height=8)
        self.patient_tree.grid(row=4, column=0, columnspan=2, pady=20)
        for col in ("ID","Name","Age","Disease"):
            self.patient_tree.heading(col, text=col)

    def add_patient(self):
        try:
            cur.execute("INSERT INTO patients(name,age,disease) VALUES(?,?,?)",
                        (self.pname.get(), int(self.page.get()), self.pdisease.get()))
            con.commit()
            messagebox.showinfo("Success", "Patient added!")
            self.view_patients()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def view_patients(self):
        for row in self.patient_tree.get_children():
            self.patient_tree.delete(row)
        cur.execute("SELECT * FROM patients")
        for r in cur.fetchall():
            self.patient_tree.insert("", "end", values=r)

    # ---------- Appointment ----------
    def appointment_tab(self):
        frame = tk.Frame(self.tab2, padx=20, pady=20)
        frame.pack(fill="both")

        tk.Label(frame, text="Patient ID").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(frame, text="Doctor Name").grid(row=1, column=0, padx=10, pady=5)
        tk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=2, column=0, padx=10, pady=5)

        self.ap_pid = tk.Entry(frame); self.ap_pid.grid(row=0, column=1)
        self.ap_doc = tk.Entry(frame); self.ap_doc.grid(row=1, column=1)
        self.ap_date = tk.Entry(frame); self.ap_date.grid(row=2, column=1)

        tk.Button(frame, text="Add Appointment", command=self.add_appointment, bg="orange").grid(row=3, column=0, columnspan=2, pady=10)

        # Treeview for appointments
        self.app_tree = ttk.Treeview(frame, columns=("ID","Patient ID","Doctor","Date"), show="headings", height=8)
        self.app_tree.grid(row=4, column=0, columnspan=2, pady=20)
        for col in ("ID","Patient ID","Doctor","Date"):
            self.app_tree.heading(col, text=col)

    def add_appointment(self):
        try:
            cur.execute("INSERT INTO appointments(patient_id,doctor,date) VALUES(?,?,?)",
                        (int(self.ap_pid.get()), self.ap_doc.get(), self.ap_date.get()))
            con.commit()
            messagebox.showinfo("Success", "Appointment added!")
            self.view_appointments()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def view_appointments(self):
        for row in self.app_tree.get_children():
            self.app_tree.delete(row)
        cur.execute("SELECT * FROM appointments")
        for r in cur.fetchall():
            self.app_tree.insert("", "end", values=r)

    # ---------- Billing ----------
    def billing_tab(self):
        frame = tk.Frame(self.tab3, padx=20, pady=20)
        frame.pack(fill="both")

        tk.Label(frame, text="Patient ID").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(frame, text="Amount").grid(row=1, column=0, padx=10, pady=5)
        tk.Label(frame, text="Details").grid(row=2, column=0, padx=10, pady=5)

        self.bill_pid = tk.Entry(frame); self.bill_pid.grid(row=0, column=1)
        self.bill_amt = tk.Entry(frame); self.bill_amt.grid(row=1, column=1)
        self.bill_det = tk.Entry(frame); self.bill_det.grid(row=2, column=1)

        tk.Button(frame, text="Generate Bill", command=self.add_bill, bg="pink").grid(row=3, column=0, columnspan=2, pady=10)

        # Treeview for bills
        self.bill_tree = ttk.Treeview(frame, columns=("ID","Patient ID","Amount","Details"), show="headings", height=8)
        self.bill_tree.grid(row=4, column=0, columnspan=2, pady=20)
        for col in ("ID","Patient ID","Amount","Details"):
            self.bill_tree.heading(col, text=col)

    def add_bill(self):
        try:
            cur.execute("INSERT INTO billing(patient_id,amount,details) VALUES(?,?,?)",
                        (int(self.bill_pid.get()), float(self.bill_amt.get()), self.bill_det.get()))
            con.commit()
            messagebox.showinfo("Success", "Bill generated!")
            self.view_bills()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def view_bills(self):
        for row in self.bill_tree.get_children():
            self.bill_tree.delete(row)
        cur.execute("SELECT * FROM billing")
        for r in cur.fetchall():
            self.bill_tree.insert("", "end", values=r)

    # ---------- Regex Search ----------
    def search_tab(self):
        frame = tk.Frame(self.tab4, padx=20, pady=20)
        frame.pack(fill="both")

        tk.Label(frame, text="Search Disease (Regex)").grid(row=0, column=0, padx=10, pady=5)
        self.search_box = tk.Entry(frame); self.search_box.grid(row=0, column=1)
        tk.Button(frame, text="Search", command=self.search_patient, bg="yellow").grid(row=1, column=0, columnspan=2, pady=10)

    def search_patient(self):
        pattern = self.search_box.get()
        cur.execute("SELECT * FROM patients")
        rows = cur.fetchall()
        matches = [f"{r[1]} ({r[3]})" for r in rows if re.search(pattern, r[3], re.IGNORECASE)]
        messagebox.showinfo("Search Result", "\n".join(matches) if matches else "No match found")
    def login_tab(self):
        frame = tk.Frame(self.tab5, padx=20, pady=20)
        frame.pack(fill="both")

        tk.Label(frame, text="Username").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(frame, text="Password").grid(row=1, column=0, padx=10, pady=5)

        self.user = tk.Entry(frame); self.user.grid(row=0, column=1)
        self.pwd = tk.Entry(frame, show="*"); self.pwd.grid(row=1, column=1)

        tk.Button(frame, text="Login", command=self.login, bg="lightgray").grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        users = {"admin":"123", "doctor":"doc", "reception":"rec"}
        try:
            if self.user.get() in users and users[self.user.get()] == self.pwd.get():
                messagebox.showinfo("Login", f"Welcome {self.user.get()}!")
            else:
                raise Exception("Invalid Credentials")
        except Exception as e:
            messagebox.showerror("Access Denied", str(e))

# ---------- Run App ----------
root = tk.Tk()
MediTrack(root)
root.mainloop()
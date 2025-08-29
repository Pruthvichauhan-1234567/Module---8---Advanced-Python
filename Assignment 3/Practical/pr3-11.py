# 11. Write a Python program to connect to an SQLite3 database, create a table, insert data, and fetch data.

import sqlite3
conn = sqlite3.connect('students.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL
    )
''')
cursor.execute("INSERT INTO students (name, age) VALUES (?, ?)", ("Alice", 22))
cursor.execute("INSERT INTO students (name, age) VALUES (?, ?)", ("Bob", 24))
conn.commit()
cursor.execute("SELECT * FROM students")
rows = cursor.fetchall()
print("Student Records:")
for row in rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Age: {row[2]}")
conn.close()

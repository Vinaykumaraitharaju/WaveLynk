import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department_name TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
)
""")

default_roles = [
    ("Admin", 1),
    ("Manager", 1),
    ("Employee", 1),
    ("HR", 1),
    ("Team Lead", 1),
    ("HOD", 1),
]

default_departments = [
    ("HR", 1),
    ("Operations", 1),
    ("Finance", 1),
    ("IT", 1),
    ("Claims", 1),
    ("Support", 1),
    ("Admin", 1),
]

for role in default_roles:
    cur.execute(
        "INSERT OR IGNORE INTO roles (role_name, is_active) VALUES (?, ?)",
        role,
    )

for dept in default_departments:
    cur.execute(
        "INSERT OR IGNORE INTO departments (department_name, is_active) VALUES (?, ?)",
        dept,
    )

conn.commit()
conn.close()

print("roles and departments tables created successfully")
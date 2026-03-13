import sqlite3
from config import DB_PATH

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("PRAGMA table_info(holidays)")
columns = [row[1] for row in cur.fetchall()]

if "optional_flag" not in columns:
    cur.execute("ALTER TABLE holidays ADD COLUMN optional_flag INTEGER NOT NULL DEFAULT 0")
    conn.commit()
    print("optional_flag column added to holidays table")
else:
    print("optional_flag already exists")

conn.close()
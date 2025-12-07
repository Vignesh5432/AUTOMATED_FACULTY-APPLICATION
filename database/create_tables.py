import sqlite3

DB_PATH = "database/exam_management.db"
SQL_FILE = "database/db.sql"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

with open(SQL_FILE, "r") as f:
    sql_script = f.read()

cursor.executescript(sql_script)

conn.commit()
conn.close()

print("✅ All SQLite tables created successfully!")

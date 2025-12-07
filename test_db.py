from database.db_connect import get_db_connection

try:
    conn = get_db_connection()
    print("✅ SQLite Database connected successfully!")
    conn.close()
except Exception as e:
    print("❌ SQLite Database connection failed!")
    print(e)

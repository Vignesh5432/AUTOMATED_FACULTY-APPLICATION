from config import get_db_connection

try:
    conn = get_db_connection()
    print("✅ Database connected successfully!")
    conn.close()
except Exception as e:
    print("❌ Database connection failed!")
    print(e)

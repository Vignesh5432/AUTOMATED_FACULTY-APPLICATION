# faculty/faculty_allocation.py
from database.db_connect import get_db_connection

def get_available_faculty(role=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if role:
        cursor.execute("""
            SELECT * FROM faculty
            WHERE availability = 'available'
            AND role = %s
        """, (role,))
    else:
        cursor.execute("""
            SELECT * FROM faculty
            WHERE availability = 'available'
        """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data
# faculty/faculty_availability.py
from database.db_connect import get_db_connection

def update_faculty_availability(faculty_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE faculty
        SET availability = %s
        WHERE faculty_id = %s
    """, (status, faculty_id))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Availability updated successfully"}
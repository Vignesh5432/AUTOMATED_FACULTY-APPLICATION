# faculty/faculty_substitute.py
from database.db_connect import get_db_connection

def assign_substitute_faculty(absent_faculty_id, date, hall):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Find a substitute
    cursor.execute("""
        SELECT faculty_id, name
        FROM faculty
        WHERE role IN ('AP', 'Professor')
        AND availability = 'available'
        AND is_reserved = 1
        LIMIT 1
    """)
    substitute = cursor.fetchone()

    if not substitute:
        return {"error": "No substitute faculty available"}

    # Step 2: Update allocation
    cursor.execute("""
        UPDATE invigilator_allocation
        SET faculty_id = %s
        WHERE faculty_id = %s AND exam_date = %s AND hall_no = %s
    """, (substitute['faculty_id'], absent_faculty_id, date, hall))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "message": "Substitute assigned successfully",
        "substitute_faculty": substitute
    }
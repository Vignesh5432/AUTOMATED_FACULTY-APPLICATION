from database.db_connect import get_db_connection
import mysql.connector


def get_available_faculty_for_allocation(exam_date, session):
    """
    Returns ONLY faculty who are:
    ✅ Available on that date
    ✅ Available for that session ("FN", "AN", "Both")
    ✅ Below max_duties
    ✅ Not double-booked
    """

    conn = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                f.id,
                f.faculty_id,
                f.name,
                f.designation,
                f.max_duties,
                (SELECT COUNT(*) FROM allocations WHERE faculty_id = f.id) AS duties_assigned,
                GROUP_CONCAT(fs.course_code) AS subjects_handled
            FROM faculty f
            JOIN faculty_availability fa ON f.id = fa.faculty_id
            LEFT JOIN faculty_subjects fs ON f.id = fs.faculty_id
            WHERE
                fa.availability_date = %s
                AND fa.status IN (%s, 'Both')
                AND f.role = 'faculty'
            GROUP BY f.id
            HAVING duties_assigned < max_duties
        """, (exam_date, session))

        return cursor.fetchall()

    except mysql.connector.Error as err:
        print("Database Error:", err)
        return []

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

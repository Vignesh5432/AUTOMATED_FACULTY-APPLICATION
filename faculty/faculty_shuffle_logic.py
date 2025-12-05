# faculty/faculty_shuffle_logic.py
from database.db_connect import get_db_connection

def shuffle_invigilators(date):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Get all hall allocations for the day
    cursor.execute("""
        SELECT ia.allocation_id, ia.hall_no, ia.faculty_id, s.subject_code
        FROM invigilator_allocation ia
        JOIN student_hall_allocation s
            ON ia.hall_no = s.hall_no
        WHERE ia.exam_date = %s
    """, (date,))
    
    allocations = cursor.fetchall()

    # Step 2: For each hall, check subject clash
    for a in allocations:
        cursor.execute("""
            SELECT subjects_handled
            FROM faculty
            WHERE faculty_id = %s
        """, (a['faculty_id'],))
        
        handled = cursor.fetchone()['subjects_handled']

        if a['subject_code'] in handled:
            # Conflict → find replacement
            cursor.execute("""
                SELECT faculty_id
                FROM faculty
                WHERE availability = 'available'
                AND subjects_handled NOT LIKE %s
                LIMIT 1
            """, ("%"+a['subject_code']+"%",))
            replacement = cursor.fetchone()

            if replacement:
                cursor.execute("""
                    UPDATE invigilator_allocation
                    SET faculty_id = %s
                    WHERE allocation_id = %s
                """, (replacement['faculty_id'], a['allocation_id']))
                conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Shuffling completed successfully"}
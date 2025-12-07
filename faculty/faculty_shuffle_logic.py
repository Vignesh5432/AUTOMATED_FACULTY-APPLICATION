from database.db_connect import get_db_connection
import mysql.connector


def shuffle_invigilators(exam_date):
    conn = None

    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # 1️⃣ Fetch all allocations for this exam date
        cursor.execute("""
            SELECT 
                a.allocation_id,
                a.hall_id,
                a.faculty_id,
                fs.course_code
            FROM allocations a
            JOIN faculty_subjects fs ON fs.faculty_id = a.faculty_id
            WHERE a.allocation_date = %s
        """, (exam_date,))

        allocations = cursor.fetchall()

        for alloc in allocations:

            # 2️⃣ Get subjects handled by this faculty
            cursor.execute("""
                SELECT GROUP_CONCAT(course_code) AS subjects
                FROM faculty_subjects
                WHERE faculty_id = %s
            """, (alloc['faculty_id'],))

            result = cursor.fetchone()
            handled_subjects = set(result['subjects'].split(',')) if result and result['subjects'] else set()

            # 3️⃣ If subject clash occurs
            if alloc['course_code'] in handled_subjects:

                # 4️⃣ Find replacement faculty
                cursor.execute("""
                    SELECT 
                        f.id,
                        f.faculty_id,
                        f.max_duties,
                        (SELECT COUNT(*) FROM allocations WHERE faculty_id = f.id) AS duties_assigned,
                        GROUP_CONCAT(fs.course_code) AS subjects_handled
                    FROM faculty f
                    JOIN faculty_availability fa ON f.id = fa.faculty_id
                    LEFT JOIN faculty_subjects fs ON f.id = fs.faculty_id
                    WHERE 
                        fa.availability_date = %s
                        AND fa.status IN ('Available','Both')
                        AND f.id != %s
                    GROUP BY f.id
                    HAVING duties_assigned < max_duties
                """, (exam_date, alloc['faculty_id']))

                candidates = cursor.fetchall()
                replacement = None

                for c in candidates:
                    subject_set = set(c['subjects_handled'].split(',')) if c['subjects_handled'] else set()

                    if alloc['course_code'] not in subject_set:

                        # ✅ Prevent same-session double assignment
                        cursor.execute("""
                            SELECT COUNT(*) FROM allocations
                            WHERE faculty_id = %s 
                            AND allocation_date = %s 
                            AND session = (
                                SELECT session FROM allocations WHERE allocation_id = %s
                            )
                        """, (c['id'], exam_date, alloc['allocation_id']))

                        if cursor.fetchone()[0] > 0:
                            continue

                        replacement = c
                        break

                # 5️⃣ Perform shuffle update safely
                if replacement:
                    cursor.execute("""
                        UPDATE allocations
                        SET faculty_id = %s
                        WHERE allocation_id = %s
                    """, (replacement['id'], alloc['allocation_id']))

        conn.commit()
        return {"message": "Shuffling completed successfully"}

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return {"error": f"Database error: {err}"}

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

from database.db_connect import get_db_connection
import mysql.connector


def assign_substitute_faculty(absent_faculty_id, exam_date, session, hall_id):
    conn = None

    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # 1️⃣ Mark absent faculty as Unavailable
        cursor.execute("""
            INSERT INTO faculty_availability (faculty_id, availability_date, status)
            VALUES (
                (SELECT id FROM faculty WHERE faculty_id = %s),
                %s,
                'Unavailable'
            )
            ON DUPLICATE KEY UPDATE status = 'Unavailable'
        """, (absent_faculty_id, exam_date))

        # 2️⃣ Fetch hall subjects
        cursor.execute("""
            SELECT GROUP_CONCAT(fs.course_code) AS courses
            FROM allocations a
            JOIN faculty_subjects fs ON fs.faculty_id = a.faculty_id
            WHERE a.hall_id = %s AND a.allocation_date = %s AND a.session = %s
        """, (hall_id, exam_date, session))

        row = cursor.fetchone()
        hall_subjects = set(row['courses'].split(',')) if row and row['courses'] else set()

        # 3️⃣ Find valid substitute faculty
        cursor.execute("""
            SELECT 
                f.id,
                f.faculty_id,
                f.name,
                f.max_duties,
                (SELECT COUNT(*) FROM allocations WHERE faculty_id = f.id) AS duties_assigned,
                GROUP_CONCAT(fs.course_code) AS subjects_handled
            FROM faculty f
            JOIN faculty_availability fa ON f.id = fa.faculty_id
            LEFT JOIN faculty_subjects fs ON f.id = fs.faculty_id
            WHERE
                fa.availability_date = %s
                AND fa.status IN ('Available','Both')
                AND f.faculty_id != %s
            GROUP BY f.id
            HAVING duties_assigned < max_duties
        """, (exam_date, absent_faculty_id))

        candidates = cursor.fetchall()
        substitute = None

        for c in candidates:
            c_subjects = set(c['subjects_handled'].split(',')) if c['subjects_handled'] else set()

            # ❌ Reject if subject conflict
            if hall_subjects & c_subjects:
                continue

            # ❌ Prevent same-session double assignment
            cursor.execute("""
                SELECT COUNT(*) FROM allocations
                WHERE faculty_id = %s
                AND allocation_date = %s
                AND session = %s
            """, (c['id'], exam_date, session))

            if cursor.fetchone()[0] > 0:
                continue

            substitute = c
            break

        if not substitute:
            conn.rollback()
            return {"error": "No eligible substitute faculty found"}

        # 4️⃣ Replace faculty safely
        cursor.execute("""
            UPDATE allocations
            SET faculty_id = %s
            WHERE faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
              AND allocation_date = %s
              AND session = %s
              AND hall_id = %s
        """, (substitute['id'], absent_faculty_id, exam_date, session, hall_id))

        conn.commit()

        return {
            "message": "Substitute assigned successfully",
            "substitute_faculty": {
                "faculty_id": substitute['faculty_id'],
                "name": substitute['name']
            }
        }

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return {"error": f"Database Error: {err}"}

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

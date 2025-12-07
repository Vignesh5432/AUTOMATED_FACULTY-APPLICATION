from . import allocation_bp
from flask import request, jsonify
from database.db_connect import get_db_connection
import mysql.connector

@allocation_bp.route('/reallocate/replace', methods=['POST'])
def replace_absent_endpoint():
    """
    POST JSON:
    {
      "absent_faculty_id": "F015",
      "exam_date": "2025-10-10",
      "session": "FN",
      "hall_id": 101
    }
    """
    data = request.get_json() or {}

    absent = data.get('absent_faculty_id')
    exam_date = data.get('exam_date')
    session = data.get('session')
    hall_id = data.get('hall_id')

    if not all([absent, exam_date, session, hall_id]):
        return jsonify({
            "error": "absent_faculty_id, exam_date, session, hall_id required"
        }), 400

    try:
        result = replace_absent_with_substitute(absent, exam_date, session, hall_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def replace_absent_with_substitute(absent_faculty_id, exam_date, session, hall_id):
    conn = None

    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # ✅ 1) Mark faculty as Unavailable for that date
        cursor.execute("""
            INSERT INTO faculty_availability (faculty_id, availability_date, status)
            VALUES (
                (SELECT id FROM faculty WHERE faculty_id = %s),
                %s,
                'Unavailable'
            )
            ON DUPLICATE KEY UPDATE status = 'Unavailable'
        """, (absent_faculty_id, exam_date))

        # ✅ Also disable absent faculty globally for safety
        cursor.execute("""
            UPDATE faculty SET is_available = 0
            WHERE faculty_id = %s
        """, (absent_faculty_id,))

        # ✅ 2) Get hall subject mapping
        cursor.execute("""
            SELECT GROUP_CONCAT(fs.course_code) AS courses
            FROM allocations a
            JOIN faculty_subjects fs ON fs.faculty_id = a.faculty_id
            WHERE a.hall_id = %s 
              AND a.allocation_date = %s 
              AND a.session = %s
        """, (hall_id, exam_date, session))

        row = cursor.fetchone()
        hall_courses = set(row['courses'].split(',')) if row and row['courses'] else set()

        # ✅ 3) Fetch all eligible available faculty
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
                fa.availability_date = %s AND
                (fa.status = 'Available' OR fa.status = 'Both') AND
                f.id != (SELECT id FROM faculty WHERE faculty_id = %s)
            GROUP BY f.id, f.faculty_id, f.name, f.max_duties
            HAVING duties_assigned < max_duties
        """, (exam_date, absent_faculty_id))

        candidates = cursor.fetchall()

        selected = None
        for faculty in candidates:

            subjects = set(faculty['subjects_handled'].split(',')) if faculty['subjects_handled'] else set()

            # ✅ Subject conflict protection
            if hall_courses & subjects:
                continue

            # ✅ No duplicate same-session assignment
            cursor.execute("""
                SELECT COUNT(*) FROM allocations
                WHERE faculty_id = %s 
                  AND allocation_date = %s 
                  AND session = %s
            """, (faculty['id'], exam_date, session))

            count = cursor.fetchone()[0]
            if count > 0:
                continue

            selected = faculty
            break

        if not selected:
            conn.rollback()
            return {"error": "No eligible substitute found"}

        # ✅ 4) Replace the allocation
        cursor.execute("""
            UPDATE allocations
            SET faculty_id = %s
            WHERE faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
              AND allocation_date = %s
              AND session = %s
              AND hall_id = %s
        """, (
            selected['id'],
            absent_faculty_id,
            exam_date,
            session,
            hall_id
        ))

        conn.commit()

        return {
            "ok": True,
            "substitute_assigned": selected['faculty_id'],
            "name": selected['name']
        }

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {err}")

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

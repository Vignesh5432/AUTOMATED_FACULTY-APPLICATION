from . import allocation_bp
from flask import request, jsonify
from database.db_connect import get_db_connection
import mysql.connector

# ✅ Config: official HOD designations used in DB
HOD_DESIGNATIONS = ("HOD", "Head", "Head of Department")


@allocation_bp.route('/hod/assign', methods=['POST'])
def assign_hod_squad_endpoint():
    """
    POST JSON:
    {
      "exam_type":"Semester" or "Internal",
      "exam_date":"YYYY-MM-DD",
      "sessions":["FN","AN"]   // optional, default both
    }
    """
    data = request.get_json() or {}

    exam_type = data.get('exam_type')
    exam_date = data.get('exam_date')
    sessions = data.get('sessions', ["FN", "AN"])

    if not exam_type or not exam_date:
        return jsonify({"error": "exam_type and exam_date required"}), 400

    try:
        count = assign_hod_squad(exam_type, exam_date, sessions)
        return jsonify({"ok": True, "assigned_count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def assign_hod_squad(exam_type, exam_date, sessions):
    """
    Assigns all eligible HODs as squad members.
    Applies:
    ✅ availability check
    ✅ max duty limit
    ✅ duplicate prevention
    ✅ transaction safety
    """

    conn = None
    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        # ✅ Fetch eligible HODs with duty count
        cursor.execute("""
            SELECT 
                f.id,
                f.faculty_id,
                f.max_duties,
                (SELECT COUNT(*) FROM allocations WHERE faculty_id = f.id) AS duties_assigned
            FROM faculty f
            JOIN faculty_availability fa ON f.id = fa.faculty_id
            WHERE 
                fa.availability_date = %s
                AND (fa.status = 'Available' OR fa.status = 'Both')
                AND f.designation IN (%s, %s, %s)
            GROUP BY f.id
            HAVING duties_assigned < max_duties
        """, (exam_date, *HOD_DESIGNATIONS))

        hods = cursor.fetchall()
        inserted = 0

        for hod in hods:
            for session in sessions:

                # ✅ Prevent duplicate assignment
                cursor.execute("""
                    SELECT COUNT(*) FROM allocations
                    WHERE faculty_id = %s AND allocation_date = %s AND session = %s
                """, (hod['id'], exam_date, session))

                if cursor.fetchone()[0] > 0:
                    continue

                # ✅ Insert squad duty
                cursor.execute("""
                    INSERT INTO allocations
                    (faculty_id, hall_id, allocation_date, session, status)
                    VALUES (%s, NULL, %s, %s, 'HOD-SQUAD')
                """, (hod['id'], exam_date, session))

                hod['duties_assigned'] += 1
                inserted += 1

        conn.commit()
        return inserted

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        raise Exception(f"Database error: {err}")

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

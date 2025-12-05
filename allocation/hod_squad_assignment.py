# allocation/hod_squad_assignment.py
from . import allocation_bp
from flask import request, jsonify
from database.db_connect import get_db_connection

# config: HOD designation values that represent heads
HOD_DESIGNATIONS = ('HOD', 'Head', 'Head of Department')

@allocation_bp.route('/hod/assign', methods=['POST'])
def assign_hod_squad_endpoint():
    """
    POST JSON:
    {
      "exam_type":"Semester" or "Internal",
      "exam_date":"YYYY-MM-DD",
      "sessions":["Forenoon","Afternoon"]   // optional, default both
    }
    """
    data = request.get_json() or {}
    exam_type = data.get('exam_type')
    exam_date = data.get('exam_date')
    sessions = data.get('sessions', ["Forenoon", "Afternoon"])

    if not exam_type or not exam_date:
        return jsonify({"error":"exam_type and exam_date required"}), 400

    try:
        count = assign_hod_squad(exam_type, exam_date, sessions)
        return jsonify({"ok": True, "assigned_count": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def assign_hod_squad(exam_type, exam_date, sessions):
    """
    Insert squad duties for all available HODs for given sessions.
    Returns number of inserted duties.
    """
    conn = get_db_connection()
    if not conn:
        raise Exception("DB connection failed")
    cursor = conn.cursor()

    # fetch available HODs
    cursor.execute("""
        SELECT faculty_id FROM faculty
        WHERE designation IN (%s, %s, %s)
        AND is_available = 1
    """, HOD_DESIGNATIONS)
    hods = [r[0] for r in cursor.fetchall()]

    inserted = 0
    for hod in hods:
        for session in sessions:
            # ensure not already assigned same date/session (prevent dup)
            cursor.execute("""
                SELECT COUNT(*) FROM invigilator_allocation
                WHERE faculty_id = %s AND exam_date = %s AND session = %s
            """, (hod, exam_date, session))
            if cursor.fetchone()[0] > 0:
                continue
            cursor.execute("""
                INSERT INTO invigilator_allocation
                (faculty_id, hall_id, exam_date, session, exam_type)
                VALUES (%s, NULL, %s, %s, %s)
            """, (hod, exam_date, session, exam_type))
            inserted += 1

    conn.commit()
    cursor.close()
    conn.close()
    return inserted
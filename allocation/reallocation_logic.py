# allocation/reallocation_logic.py
from . import allocation_bp
from flask import request, jsonify
from database.db_connect import get_db_connection

@allocation_bp.route('/reallocate/replace', methods=['POST'])
def replace_absent_endpoint():
    """
    POST JSON:
    {
      "absent_faculty_id": "F015",
      "exam_date": "2025-10-10",
      "session": "Forenoon",
      "hall_id": 101
    }
    """
    data = request.get_json() or {}
    absent = data.get('absent_faculty_id')
    exam_date = data.get('exam_date')
    session = data.get('session')
    hall_id = data.get('hall_id')

    if not all([absent, exam_date, session, hall_id]):
        return jsonify({"error":"absent_faculty_id, exam_date, session, hall_id required"}), 400

    try:
        result = replace_absent_with_substitute(absent, exam_date, session, hall_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def replace_absent_with_substitute(absent_faculty_id, exam_date, session, hall_id):
    conn = get_db_connection()
    if not conn:
        raise Exception("DB connection failed")
    cursor = conn.cursor(dictionary=True)

    # 1) mark absent in faculty_availability (optional - but ensure record)
    cursor.execute("""
        INSERT INTO faculty_availability (faculty_id, unavailable_date, reason)
        VALUES (%s, %s, %s)
    """, (absent_faculty_id, exam_date, "Marked absent via reconciliation"))
    conn.commit()

    # 2) find substitute faculty from substitute_faculty table who is reserved and available
    cursor.execute("""
        SELECT sf.faculty_id, f.subject_1, f.subject_2, f.subject_3
        FROM substitute_faculty sf
        JOIN faculty f ON sf.faculty_id = f.faculty_id
        WHERE sf.is_reserved = 1 AND f.is_available = 1
    """)
    candidates = cursor.fetchall()

    if not candidates:
        cursor.close()
        conn.close()
        return {"error": "No substitute faculty reserved/available"}

    # fetch hall courses to enforce subject mismatch
    cursor.execute("""
        SELECT GROUP_CONCAT(course_id) AS courses 
        FROM hall_allocation
        WHERE hall_id = %s AND exam_date = %s AND session = %s
    """, (hall_id, exam_date, session))
    row = cursor.fetchone()
    hall_courses = set()
    if row and row['courses']:
        hall_courses = set(row['courses'].split(','))

    selected = None
    for c in candidates:
        subj_set = set()
        for s in (c['subject_1'], c['subject_2'], c['subject_3']):
            if s:
                subj_set.add(s)
        # subject mismatch check
        if hall_courses & subj_set:
            continue
        # ensure not already assigned same session
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM invigilator_allocation
            WHERE faculty_id = %s AND exam_date = %s AND session = %s
        """, (c['faculty_id'], exam_date, session))
        if cursor.fetchone()['cnt'] > 0:
            continue

        selected = c
        break

    if not selected:
        cursor.close()
        conn.close()
        return {"error":"No eligible substitute found (subject/availability conflict)"}

    # 3) perform update in invigilator_allocation: replace absent faculty
    cursor.execute("""
        UPDATE invigilator_allocation
        SET faculty_id = %s
        WHERE faculty_id = %s AND exam_date = %s AND session = %s AND hall_id = %s
    """, (selected['faculty_id'], absent_faculty_id, exam_date, session, hall_id))
    conn.commit()

    # 4) mark substitute as no longer reserved (optionally)
    cursor.execute("""
        UPDATE substitute_faculty SET is_reserved = 0 WHERE faculty_id = %s
    """, (selected['faculty_id'],))
    conn.commit()

    cursor.close()
    conn.close()

    return {"ok": True, "substitute_assigned": selected['faculty_id']}
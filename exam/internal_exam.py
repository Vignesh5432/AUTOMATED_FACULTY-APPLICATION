# exam/internal_exam.py
from . import exam_bp, _execute, _to_date
from flask import request, jsonify

@exam_bp.route('/internal/create', methods=['POST'])
def create_internal_exam():
    """
    POST JSON:
    {
      "exam_date": "2025-09-05",
      "session": "Forenoon" | "Afternoon",
      "course_id": "CS201"
    }
    """
    data = request.get_json() or {}
    exam_date = data.get('exam_date')
    session = data.get('session')
    course_id = data.get('course_id')

    if not exam_date or not session or not course_id:
        return jsonify({"error":"exam_date, session and course_id required"}), 400

    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error":"exam_date must be YYYY-MM-DD"}), 400

    q = """INSERT INTO exam_schedule (exam_type, exam_date, session, course_id)
           VALUES (%s, %s, %s, %s)"""
    res = _execute(q, ("Internal", exam_date, session, course_id))
    if isinstance(res, tuple) and res[1] == 500:
        return jsonify(res[0]), 500
    return jsonify({"ok": True, "message":"Internal exam created"}), 201


@exam_bp.route('/internal/list', methods=['GET'])
def list_internal_exams():
    q = "SELECT * FROM exam_schedule WHERE exam_type = 'Internal' ORDER BY exam_date, session"
    res = _execute(q, fetch=True)
    if isinstance(res, tuple) and res[1] == 500:
        return jsonify(res[0]), 500
    return jsonify(res), 200
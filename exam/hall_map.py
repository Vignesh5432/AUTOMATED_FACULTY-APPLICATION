# exam/hall_map.py
from . import exam_bp, _execute, _to_date
from flask import request, jsonify

@exam_bp.route('/hall/map', methods=['POST'])
def map_course_to_hall():
    """
    POST JSON:
    {
      "hall_id": 101,
      "course_id": "CS301",
      "exam_date": "2025-10-10",
      "session": "Forenoon"
    }
    Can be called multiple times with the same hall_id to record multiple courses for that hall.
    """
    data = request.get_json() or {}
    hall_id = data.get('hall_id')
    course_id = data.get('course_id')
    exam_date = data.get('exam_date')
    session = data.get('session')

    if not hall_id or not course_id or not exam_date or not session:
        return jsonify({"error":"hall_id, course_id, exam_date, session required"}), 400

    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error":"exam_date must be YYYY-MM-DD"}), 400

    q = """INSERT INTO hall_allocation (hall_id, course_id, exam_date, session)
           VALUES (%s, %s, %s, %s)"""
    res = _execute(q, (hall_id, course_id, exam_date, session))
    if isinstance(res, tuple) and res[1] == 500:
        return jsonify(res[0]), 500
    return jsonify({"ok": True, "message":"Course mapped to hall"}), 201


@exam_bp.route('/hall/list', methods=['GET'])
def list_hall_courses():
    """
    Query params: exam_date=YYYY-MM-DD & session=Forenoon|Afternoon (optional)
    Returns hall -> list of courses mapped for that date/session
    """
    exam_date = request.args.get('exam_date')
    session = request.args.get('session')

    if not exam_date:
        return jsonify({"error":"exam_date query parameter required"}), 400
    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error":"exam_date must be YYYY-MM-DD"}), 400

    if session:
        q = """SELECT hall_id, GROUP_CONCAT(course_id) AS courses
               FROM hall_allocation
               WHERE exam_date = %s AND session = %s
               GROUP BY hall_id"""
        res = _execute(q, (exam_date, session), fetch=True)
    else:
        q = """SELECT hall_id, session, GROUP_CONCAT(course_id) AS courses
               FROM hall_allocation
               WHERE exam_date = %s
               GROUP BY hall_id, session"""
        res = _execute(q, (exam_date,), fetch=True)

    if isinstance(res, tuple) and res[1] == 500:
        return jsonify(res[0]), 500
    # parse GROUP_CONCAT results -> arrays
    for row in res:
        if 'courses' in row and row['courses'] is not None:
            row['courses'] = row['courses'].split(',')
    return jsonify(res), 200
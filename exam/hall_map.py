# exam/hall_map.py
from . import exam_bp
from flask import request, jsonify
from database.db_connect import get_db_connection
import mysql.connector
from datetime import datetime

# -----------------------------------------------------
# ✅ INTERNAL SAFE HELPERS (REPLACES _execute, _to_date)
# -----------------------------------------------------

def _to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def _execute(query, params=None, fetch=False):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = {"ok": True}

        return result

    except mysql.connector.Error as err:
        return {"error": str(err)}, 500

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# -----------------------------------------------------
# ✅ MAP COURSE TO HALL
# -----------------------------------------------------

@exam_bp.route('/hall/map', methods=['POST'])
def map_course_to_hall():
    data = request.get_json() or {}

    hall_id = data.get('hall_id')
    course_id = data.get('course_id')
    exam_date = data.get('exam_date')
    session = data.get('session')

    if not all([hall_id, course_id, exam_date, session]):
        return jsonify({"error": "hall_id, course_id, exam_date, session required"}), 400

    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error": "exam_date must be YYYY-MM-DD"}), 400

    q = """
        INSERT INTO hall_allocation (hall_id, course_id, exam_date, session)
        VALUES (%s, %s, %s, %s)
    """

    res = _execute(q, (hall_id, course_id, exam_date, session))

    if isinstance(res, tuple):
        return jsonify(res[0]), 500

    return jsonify({"ok": True, "message": "Course mapped to hall"}), 201

# -----------------------------------------------------
# ✅ LIST HALL → COURSES
# -----------------------------------------------------

@exam_bp.route('/hall/list', methods=['GET'])
def list_hall_courses():
    exam_date = request.args.get('exam_date')
    session = request.args.get('session')

    if not exam_date:
        return jsonify({"error": "exam_date query parameter required"}), 400

    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error": "exam_date must be YYYY-MM-DD"}), 400

    if session:
        q = """
            SELECT hall_id, GROUP_CONCAT(course_id) AS courses
            FROM hall_allocation
            WHERE exam_date = %s AND session = %s
            GROUP BY hall_id
        """
        res = _execute(q, (exam_date, session), fetch=True)
    else:
        q = """
            SELECT hall_id, session, GROUP_CONCAT(course_id) AS courses
            FROM hall_allocation
            WHERE exam_date = %s
            GROUP BY hall_id, session
        """
        res = _execute(q, (exam_date,), fetch=True)

    if isinstance(res, tuple):
        return jsonify(res[0]), 500

    for row in res:
        if row['courses']:
            row['courses'] = row['courses'].split(',')

    return jsonify(res), 200

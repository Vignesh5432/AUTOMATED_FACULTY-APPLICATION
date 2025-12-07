# exam/internal_exam.py
from . import exam_bp
from flask import request, jsonify
from database.db_connect import get_db_connection
import mysql.connector
from datetime import datetime


# --------------------------------------------------
# ✅ DATE VALIDATOR
# --------------------------------------------------
def _to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")


# --------------------------------------------------
# ✅ CREATE INTERNAL EXAM
# --------------------------------------------------
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
        return jsonify({"error": "exam_date, session and course_id required"}), 400

    try:
        _to_date(exam_date)
    except ValueError:
        return jsonify({"error": "exam_date must be YYYY-MM-DD"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO exam_schedule (exam_type, exam_date, session, course_id)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, ("Internal", exam_date, session, course_id))
        conn.commit()

        return jsonify({"ok": True, "message": "Internal exam created"}), 201

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return jsonify({"error": str(err)}), 500

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# --------------------------------------------------
# ✅ LIST INTERNAL EXAMS
# --------------------------------------------------
@exam_bp.route('/internal/list', methods=['GET'])
def list_internal_exams():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM exam_schedule
            WHERE exam_type = 'Internal'
            ORDER BY exam_date, session
        """)

        result = cursor.fetchall()
        return jsonify(result), 200

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500

    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

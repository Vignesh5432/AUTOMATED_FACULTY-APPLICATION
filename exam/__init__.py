# exam/__init__.py

from flask import Blueprint, request, jsonify
from database.db_connect import get_db_connection
from datetime import datetime

# ✅ FIXED HERE
exam_bp = Blueprint('exam', __name__, url_prefix='/exam')

# -------- helpers --------

def _to_date(date_str):
    """Convert YYYY-MM-DD string to date object. Raises ValueError if invalid."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def _execute(query, params=None, fetch=False):
    conn = get_db_connection()
    if not conn:
        return {"error": "DB connection failed"}, 500

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        else:
            conn.commit()
            cursor.close()
            conn.close()
            return {"ok": True}

    except Exception as e:
        try:
            conn.close()
        except:
            pass
        return {"error": str(e)}, 500

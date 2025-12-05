# faculty/faculty_routes.py
from flask import Blueprint, request, jsonify
from database.db_connect import get_db_connection

# NEW IMPORTS for allocation
from .faculty_allocation import allocate_faculty_by_students, save_allocation_to_db

# Existing imports
from .faculty_availability import update_faculty_availability
from .faculty_substitute import assign_substitute_faculty
from .faculty_shuffle_logic import shuffle_invigilators

faculty_bp = Blueprint('faculty_bp', __name__)

# --------------------------
# GET ALL FACULTY LIST
# --------------------------
@faculty_bp.route('/faculty/all', methods=['GET'])
def get_all_faculty():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM faculty")
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(data)

# ------------------------------------------------------
# RUN FACULTY ALLOCATION (students ÷ 30 rule)
# ------------------------------------------------------
@faculty_bp.route('/faculty/allocate', methods=['POST'])
def allocate_faculty():
    """
    Runs the allocation:
    - students ÷ 30 = required faculty
    - Allocates lowest designation first
    - Saves allocation into DB
    """
    allocation_data = allocate_faculty_by_students()
    save_allocation_to_db(allocation_data)

    return jsonify({
        "message": "Faculty allocation completed successfully!",
        "allocation": allocation_data
    })

# ------------------------------------------------------
# UPDATE FACULTY AVAILABILITY
# ------------------------------------------------------
@faculty_bp.route('/faculty/availability', methods=['POST'])
def faculty_mark_availability():
    faculty_id = request.json.get("faculty_id")
    status = request.json.get("status")  # available / unavailable

    result = update_faculty_availability(faculty_id, status)
    return jsonify(result)

# ------------------------------------------------------
# ASSIGN SUBSTITUTE FACULTY
# ------------------------------------------------------
@faculty_bp.route('/faculty/substitute', methods=['POST'])
def substitute_faculty():
    original_faculty = request.json.get("original_faculty_id")
    date = request.json.get("date")
    hall = request.json.get("hall")

    result = assign_substitute_faculty(original_faculty, date, hall)
    return jsonify(result)

# ------------------------------------------------------
# SHUFFLE INVIGILATORS TO AVOID SUBJECT CLASH
# ------------------------------------------------------
@faculty_bp.route('/faculty/shuffle', methods=['POST'])
def shuffle_faculty_api():
    date = request.json.get("date")
    result = shuffle_invigilators(date)
    return jsonify(result)

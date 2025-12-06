from flask import Blueprint, render_template, session, redirect, flash
from database.db_connect import get_db_connection
import mysql.connector
from functools import wraps

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

# Decorator to ensure user is a logged-in faculty member
def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'faculty':
            flash("You must be logged in as a faculty member to view this page.", "warning")
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@faculty_bp.route("/dashboard")
@faculty_required
def dashboard():
    allocations = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        faculty_id = session.get('faculty_id')

        # Fetch recent or upcoming allocations for the faculty dashboard
        cursor.execute("""
            SELECT a.allocation_id, e.exam_name, r.room_name, a.allocation_date, a.status
            FROM allocations a
            JOIN exams e ON a.exam_id = e.exam_id
            JOIN rooms r ON a.room_id = r.room_id
            WHERE a.faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
            ORDER BY a.allocation_date DESC
            LIMIT 10
        """, (faculty_id,))
        allocations = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            
    return render_template("faculty_dashboard.html", allocations=allocations)


@faculty_bp.route("/availability")
@faculty_required
def availability():
    availabilities = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT availability_id, availability_date, status
            FROM faculty_availability
            WHERE faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
            ORDER BY availability_date DESC
        """, (faculty_id,))
        availabilities = cursor.fetchall()
        
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template("faculty_availability.html", availabilities=availabilities)


@faculty_bp.route("/allocation_view")
@faculty_required
def allocation_view():
    allocations = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        faculty_id = session.get('faculty_id')

        # Fetch all allocations for the logged-in faculty
        cursor.execute("""
            SELECT a.allocation_id, e.exam_name, r.room_name, a.allocation_date, a.session, a.status
            FROM allocations a
            JOIN exams e ON a.exam_id = e.exam_id
            JOIN rooms r ON a.room_id = r.room_id
            WHERE a.faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
            ORDER BY a.allocation_date DESC, a.session
        """, (faculty_id,))
        allocations = cursor.fetchall()

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template("faculty_allocation_view.html", allocations=allocations)


@faculty_bp.route("/substitute")
@faculty_required
def substitute_faculty():
    substitutions = []
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        faculty_id_from_session = session.get('faculty_id')

        # Fetch cases where the logged-in faculty was either the original or the substitute
        cursor.execute("""
            SELECT 
                s.substitution_id,
                a.allocation_date,
                e.exam_name,
                r.room_name,
                orig_f.name as original_faculty,
                sub_f.name as substitute_faculty,
                s.status
            FROM substitutions s
            JOIN allocations a ON s.allocation_id = a.allocation_id
            JOIN exams e ON a.exam_id = e.exam_id
            JOIN rooms r ON a.room_id = r.room_id
            JOIN faculty orig_fac_map ON s.original_faculty_id = orig_fac_map.id
            JOIN users orig_f ON orig_fac_map.user_id = orig_f.id
            JOIN faculty sub_fac_map ON s.substitute_faculty_id = sub_fac_map.id
            JOIN users sub_f ON sub_fac_map.user_id = sub_f.id
            WHERE orig_fac_map.faculty_id = %s OR sub_fac_map.faculty_id = %s
            ORDER BY a.allocation_date DESC
        """, (faculty_id_from_session, faculty_id_from_session))
        substitutions = cursor.fetchall()
        
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template("substitute_faculty.html", substitutions=substitutions)


@faculty_bp.route("/allocation_status")
@faculty_required
def allocation_status():
    stats = {'confirmed': 0, 'pending': 0, 'cancelled': 0}
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        faculty_id = session.get('faculty_id')

        # Fetch allocation status counts
        cursor.execute("""
            SELECT
                SUM(CASE WHEN status = 'Confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM allocations
            WHERE faculty_id = (SELECT id FROM faculty WHERE faculty_id = %s)
        """, (faculty_id,))
        result = cursor.fetchone()
        if result:
            stats['confirmed'] = result['confirmed'] or 0
            stats['pending'] = result['pending'] or 0
            stats['cancelled'] = result['cancelled'] or 0

    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template("allocation_status.html", stats=stats)
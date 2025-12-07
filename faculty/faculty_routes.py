from flask import Blueprint, render_template, session, redirect, flash
from database.db_connect import get_db_connection
from functools import wraps

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")


# ✅ Faculty Login Protection
def faculty_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'faculty':
            flash("You must be logged in as a faculty member.", "warning")
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# ✅ FACULTY DASHBOARD
@faculty_bp.route("/dashboard")
@faculty_required
def dashboard():
    allocations = []
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT 
                allocation_id,
                exam_date,
                session,
                hall_no,
                status
            FROM invigilator_allocation
            WHERE faculty_id = ?
            ORDER BY exam_date DESC
            LIMIT 10
        """, (faculty_id,))

        rows = cursor.fetchall()

        # ✅ Convert tuples → dicts (for Jinja templates)
        for row in rows:
            allocations.append({
                "allocation_id": row[0],
                "exam_date": row[1],
                "session": row[2],
                "hall_no": row[3],
                "status": row[4]
            })

    except Exception as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("faculty_dashboard.html", allocations=allocations)


# ✅ FACULTY AVAILABILITY VIEW
@faculty_bp.route("/availability")
@faculty_required
def availability():
    availabilities = []
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT availability_id, exam_date, is_available
            FROM faculty_availability
            WHERE faculty_id = ?
            ORDER BY exam_date DESC
        """, (faculty_id,))

        rows = cursor.fetchall()

        for row in rows:
            availabilities.append({
                "availability_id": row[0],
                "exam_date": row[1],
                "status": row[2]
            })

    except Exception as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("faculty_availability.html", availabilities=availabilities)


# ✅ FULL ALLOCATION VIEW
@faculty_bp.route("/allocation_view")
@faculty_required
def allocation_view():
    allocations = []
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT 
                allocation_id,
                exam_date,
                session,
                hall_no,
                status
            FROM invigilator_allocation
            WHERE faculty_id = ?
            ORDER BY exam_date DESC, session
        """, (faculty_id,))

        rows = cursor.fetchall()

        for row in rows:
            allocations.append({
                "allocation_id": row[0],
                "exam_date": row[1],
                "session": row[2],
                "hall_no": row[3],
                "status": row[4]
            })

    except Exception as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("faculty_allocation_view.html", allocations=allocations)


# ✅ SUBSTITUTE HISTORY
@faculty_bp.route("/substitute")
@faculty_required
def substitute_faculty():
    substitutions = []
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT 
                allocation_id,
                exam_date,
                hall_no,
                status
            FROM invigilator_allocation
            WHERE faculty_id = ?
            AND status = 'Substituted'
            ORDER BY exam_date DESC
        """, (faculty_id,))

        rows = cursor.fetchall()

        for row in rows:
            substitutions.append({
                "allocation_id": row[0],
                "exam_date": row[1],
                "hall_no": row[2],
                "status": row[3]
            })

    except Exception as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("substitute_faculty.html", substitutions=substitutions)


# ✅ ALLOCATION STATUS COUNTS
@faculty_bp.route("/allocation_status")
@faculty_required
def allocation_status():
    stats = {'confirmed': 0, 'pending': 0, 'cancelled': 0}
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        faculty_id = session.get('faculty_id')

        cursor.execute("""
            SELECT
                SUM(CASE WHEN status = 'Confirmed' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END)
            FROM invigilator_allocation
            WHERE faculty_id = ?
        """, (faculty_id,))

        result = cursor.fetchone()
        if result:
            stats['confirmed'] = result[0] or 0
            stats['pending'] = result[1] or 0
            stats['cancelled'] = result[2] or 0

    except Exception as err:
        flash(f"Database error: {err}", "danger")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template("allocation_status.html", stats=stats)

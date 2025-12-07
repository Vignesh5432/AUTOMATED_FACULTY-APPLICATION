from flask import Blueprint, request, render_template, redirect, session, url_for
from database.db_connect import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    
    conn = None       # ✅ Prevents UnboundLocalError
    cursor = None    # ✅ Prevents UnboundLocalError

    if request.method == 'POST':

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return render_template("login.html", error="Email and password are required.")

        try:
            conn = get_db_connection()

            # ✅ SQLite does NOT support dictionary=True
            # So we use normal cursor and map manually
            cursor = conn.cursor()

            cursor.execute("""
                SELECT u.id, u.email, u.password, u.role, f.faculty_id
                FROM users u
                JOIN faculty f ON u.id = f.user_id
                WHERE u.email = ? AND u.role = 'faculty'
            """, (email,))

            user = cursor.fetchone()

            # ✅ Map tuple result to variables (SQLite fix)
            if user:
                user_id, user_email, user_password, user_role, faculty_id = user
            else:
                user_id = None

            # ✅ Plain text password comparison (UNCHANGED LOGIC)
            if user and user_password == password:
                session.clear()
                session['user_id'] = user_id
                session['role'] = user_role
                session['faculty_id'] = faculty_id
                return redirect(url_for('faculty.dashboard'))

            return render_template("login.html", error="Invalid Email or Password")

        except Exception as e:
            print("DB ERROR:", e)
            return render_template("login.html", error="Internal database error")

        finally:
            # ✅ Safe close
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    return render_template("login.html")

# ✅ LOGOUT ROUTE
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

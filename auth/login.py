from flask import Blueprint, request, render_template, redirect, flash
from database.db_connect import get_db_connection
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        role = request.form.get('role')

        # ✅ Handle FACULTY login using Faculty ID
        if role == 'faculty':
            faculty_id = request.form.get('faculty_id')
            password = request.form.get('password')

            print("Faculty Login:", faculty_id, password)  # DEBUG

            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT users.*, faculty.faculty_id
                FROM users
                JOIN faculty ON users.id = faculty.user_id
                WHERE faculty.faculty_id = %s AND users.role = 'faculty'
            """, (faculty_id,))

            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password'], password):
                return redirect('/faculty/dashboard')
            else:
                flash("Invalid Faculty ID or Password")
                return redirect('/login')

        flash("Invalid role selected")
        return redirect('/login')

    return render_template("login.html")

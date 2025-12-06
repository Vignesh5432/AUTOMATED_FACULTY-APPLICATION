from flask import Blueprint, request, render_template, redirect, flash, session
from database.db_connect import get_db_connection
from werkzeug.security import check_password_hash
import mysql.connector

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        password = request.form.get('password')
        conn = None  # Initialize conn to None

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            user = None
            if role == 'faculty':
                faculty_id = request.form.get('faculty_id')
                if not faculty_id or not password:
                    flash("Faculty ID and password are required.")
                    return redirect('/login')

                cursor.execute("""
                    SELECT u.*, f.faculty_id
                    FROM users u JOIN faculty f ON u.id = f.user_id
                    WHERE f.faculty_id = %s AND u.role = 'faculty'
                """, (faculty_id,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    session['faculty_id'] = user['faculty_id']
                    return redirect('/faculty/dashboard')
                else:
                    flash("Invalid Faculty ID or Password")
                    return redirect('/login')

            elif role == 'admin':
                username = request.form.get('username')
                if not username or not password:
                    flash("Username and password are required.")
                    return redirect('/login')

                cursor.execute("SELECT * FROM users WHERE username = %s AND role = 'admin'", (username,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    return redirect('/admin/dashboard') # Assuming an admin dashboard exists
                else:
                    flash("Invalid Admin username or Password")
                    return redirect('/login')

            # Assuming 'student' role and a 'students' table similar to faculty
            elif role == 'student':
                student_id = request.form.get('student_id')
                if not student_id or not password:
                    flash("Student ID and password are required.")
                    return redirect('/login')
                
                cursor.execute("""
                    SELECT u.*, s.student_id
                    FROM users u JOIN students s ON u.id = s.user_id
                    WHERE s.student_id = %s AND u.role = 'student'
                """, (student_id,))
                user = cursor.fetchone()

                if user and check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['role'] = user['role']
                    session['student_id'] = user['student_id']
                    return redirect('/student/dashboard') # Assuming a student dashboard exists
                else:
                    flash("Invalid Student ID or Password")
                    return redirect('/login')

            else:
                flash("Invalid role selected")
                return redirect('/login')

        except mysql.connector.Error as err:
            flash(f"Database error: {err}")
            return redirect('/login')
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    return render_template("login.html")
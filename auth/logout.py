from flask import Blueprint, redirect, url_for, session, flash

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('auth.login'))

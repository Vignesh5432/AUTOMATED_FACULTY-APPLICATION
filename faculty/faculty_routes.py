from flask import Blueprint, render_template, session

faculty_bp = Blueprint("faculty", __name__, url_prefix="/faculty")

@faculty_bp.route("/dashboard")
def dashboard():
    # Fake data for now (DB will replace later)
    allocations = []
    return render_template("faculty_dashboard.html", allocations=allocations)


@faculty_bp.route("/availability")
def availability():
    availabilities = []
    return render_template("faculty_availability.html", availabilities=availabilities)


@faculty_bp.route("/allocation_view")
def allocation_view():
    allocations = []
    return render_template("faculty_allocation_view.html", allocations=allocations)


@faculty_bp.route("/substitute")
def substitute_faculty():
    substitutions = []
    return render_template("substitute_faculty.html", substitutions=substitutions)


@faculty_bp.route("/allocation_status")
def allocation_status():
    stats = [0, 0, 0]
    return render_template("allocation_status.html", stats=stats)

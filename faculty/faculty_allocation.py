import math
from database.db_connect import get_db_connection

# Priority list (LOWEST designation gets allocated FIRST)
DESIGNATION_PRIORITY = [
    "Assistant Professor",
    "Associate Professor",
    "Professor"
]


# ---------------------- Helper Functions ----------------------

def sort_faculty_by_designation(faculty_list):
    """Sort faculty: Assistant → Associate → Professor."""
    return sorted(
        faculty_list,
        key=lambda x: DESIGNATION_PRIORITY.index(x["designation"])
    )


def get_all_faculty():
    """Fetch all faculty from DB and return sorted list."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT faculty_id, faculty_name, department, designation
        FROM faculty
        ORDER BY designation
    """)
    rows = cursor.fetchall()
    conn.close()

    faculty = [
        {
            "faculty_id": row[0],
            "faculty_name": row[1],
            "department": row[2],
            "designation": row[3]
        }
        for row in rows
    ]

    return sort_faculty_by_designation(faculty)


def get_departments():
    """Fetch department names and student counts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT department_name, student_count
        FROM departments
    """)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "department_name": row[0],
            "student_count": row[1]
        }
        for row in rows
    ]


# ---------------------- Allocation Logic ----------------------

def allocate_faculty_by_students():
    """
    Main Logic:
    - required faculty = ceil(students ÷ 30)
    - Assign lowest rank first: AP -> ASP -> PROF
    - Continues until faculty list is exhausted
    """
    departments = get_departments()
    faculty_list = get_all_faculty()

    pointer = 0   # tracks which faculty is next in the ordered list
    allocations = []

    for dept in departments:
        dept_name = dept["department_name"]
        students = dept["student_count"]

        # Rule: One faculty per 30 students
        required = math.ceil(students / 30)

        allocated = []

        for _ in range(required):
            if pointer < len(faculty_list):
                allocated.append(faculty_list[pointer])
                pointer += 1
            else:
                # No more faculty available
                break

        allocations.append({
            "department": dept_name,
            "students": students,
            "required_faculty": required,
            "allocated_faculty": allocated
        })

    return allocations


# ---------------------- Save to DB ----------------------

def save_allocation_to_db(allocation_data):
    """Clear old allocations and insert new ones."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Remove previously stored allocations
    cursor.execute("DELETE FROM faculty_allocation;")

    # Save new allocation
    for dept in allocation_data:
        dept_name = dept["department"]
        for fac in dept["allocated_faculty"]:
            cursor.execute("""
                INSERT INTO faculty_allocation (department, faculty_id)
                VALUES (%s, %s)
            """, (dept_name, fac["faculty_id"]))

    conn.commit()
    conn.close()

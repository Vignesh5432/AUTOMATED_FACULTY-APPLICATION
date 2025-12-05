from database.db_connect import get_connection
import random


# -----------------------------------------
# 1. Sort based on designation priority
# -----------------------------------------
def sort_by_designation_priority(faculty_list):

    priority = {
        "Assistant Professor": 1,
        "Associate Professor": 2,
        "Professor": 3
    }

    # Shuffle inside same designation group to avoid same order always
    random.shuffle(faculty_list)

    faculty_list.sort(key=lambda x: priority.get(x['designation'], 99))

    return faculty_list


# -----------------------------------------
# 2. Get eligible faculty for invigilation
# -----------------------------------------
def get_eligible_faculty(exam_courses, exam_date, session):
    """
    exam_courses = list of course codes in that hall (because students from multiple depts)
    session = FN / AN / Both
    """

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Query: fetch faculty + subjects they handle
    query = """
        SELECT f.faculty_id, f.name, f.designation, f.department, f.max_duties, 
               GROUP_CONCAT(s.course_code) AS subjects_handled
        FROM faculty f
        LEFT JOIN faculty_subjects s ON f.faculty_id = s.faculty_id
        WHERE f.role = 'faculty'
        GROUP BY f.faculty_id;
    """
    cursor.execute(query)
    data = cursor.fetchall()

    eligible = []

    for fac in data:
        subjects = []
        if fac["subjects_handled"]:
            subjects = fac["subjects_handled"].split(",")

        # CHECK 1 – Subject clash: Faculty shouldn't invigilate their own subject exam
        if any(course in subjects for course in exam_courses):
            continue

        # CHECK 2 – Check availability
        if not is_faculty_available(fac["faculty_id"], exam_date, session):
            continue

        # CHECK 3 – Duty load balance (faculty cannot exceed max duties)
        if not has_duty_capacity(fac["faculty_id"], fac["max_duties"]):
            continue

        eligible.append(fac)

    conn.close()
    return eligible


# -----------------------------------------
# 3. Check faculty availability
# -----------------------------------------
def is_faculty_available(faculty_id, exam_date, session):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT * FROM faculty_availability
        WHERE faculty_id = %s AND date = %s AND session = %s AND status = 'available';
    """

    cursor.execute(query, (faculty_id, exam_date, session))
    result = cursor.fetchone()
    conn.close()

    return result is not None


# -----------------------------------------
# 4. Check faculty duty load limit
# -----------------------------------------
def has_duty_capacity(faculty_id, max_duties):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT COUNT(*) FROM invigilation_allocation
        WHERE faculty_id = %s;
    """

    cursor.execute(query, (faculty_id,))
    duty_count = cursor.fetchone()[0]
    conn.close()

    return duty_count < max_duties


# -----------------------------------------
# 5. ALLOCATE INVIGILATOR FOR ONE HALL
# -----------------------------------------
def allocate_invigilator_for_hall(hall_id, exam_courses, exam_date, session):
    """
    exam_courses = multiple courses inside the hall (multi-department students)
    """

    eligible = get_eligible_faculty(exam_courses, exam_date, session)

    if not eligible:
        return None  # no faculty available

    # Apply your rule: Assistant → Associate → Professor
    eligible = sort_by_designation_priority(eligible)

    # Pick the top (lowest designation)
    selected = eligible[0]

    save_invigilation(hall_id, selected["faculty_id"], exam_date, session)

    return selected


# -----------------------------------------
# 6. SAVE ALLOCATION
# -----------------------------------------
def save_invigilation(hall_id, faculty_id, exam_date, session):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO invigilation_allocation (hall_id, faculty_id, exam_date, session)
        VALUES (%s, %s, %s, %s);
    """

    cursor.execute(query, (hall_id, faculty_id, exam_date, session))
    conn.commit()
    conn.close()


# -----------------------------------------
# 7. ALLOCATE FOR MULTIPLE HALLS
# -----------------------------------------
def allocate_all_halls(hall_exam_mapping, exam_date, session):
    """
    hall_exam_mapping = {
        "H101": ["CSE101", "AIML102"],
        "H102": ["ECE201"],
        "H103": ["CSE101", "IT105", "AIDS110"]
    }
    """

    allocation_results = {}

    for hall, exam_courses in hall_exam_mapping.items():
        allocated = allocate_invigilator_for_hall(hall, exam_courses, exam_date, session)

        allocation_results[hall] = allocated

    return allocation_results
# allocation/invigilator_assignment.py
import random
import mysql.connector
from database.db_connect import get_db_connection

# -----------------------------------------
# 1. Main Allocation Orchestrator
# -----------------------------------------
def allocate_invigilators_for_session(hall_exam_mapping, exam_date, session):
    """
    Main orchestrator for allocating invigilators for a given exam session.
    This function is transactional. It will either allocate for all halls successfully
    or roll back all changes if any part of the process fails.
    """
    conn = None
    cursor = None
    results = {
        "allocations": {},
        "unallocated_halls": [],
        "error": None
    }
    
    try:
        conn = get_db_connection()
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True)

        available_faculty = _get_available_faculty_for_session(cursor, exam_date, session)
        assigned_faculty_ids_this_session = set()

        for hall_id, course_codes in hall_exam_mapping.items():
            eligible_candidates = []

            for faculty in available_faculty:
                if faculty['id'] in assigned_faculty_ids_this_session:
                    continue
                
                subjects_handled = faculty['subjects_handled'].split(',') if faculty['subjects_handled'] else []
                if any(course in subjects_handled for course in course_codes):
                    continue
                
                if faculty['duties_assigned'] >= faculty['max_duties']:
                    continue

                eligible_candidates.append(faculty)

            if not eligible_candidates:
                results["unallocated_halls"].append({hall_id: "No eligible faculty available."})
                continue
            
            _sort_by_designation_priority(eligible_candidates)
            selected_faculty = eligible_candidates[0]

            _save_invigilation_duty(cursor, hall_id, selected_faculty['id'], exam_date, session)
            
            assigned_faculty_ids_this_session.add(selected_faculty['id'])
            selected_faculty['duties_assigned'] += 1
            
            results["allocations"][hall_id] = {
                "faculty_id": selected_faculty["faculty_id"],
                "name": selected_faculty["name"],
                "designation": selected_faculty["designation"]
            }

        conn.commit()
        
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        results["error"] = f"Database transaction failed: {err}"
    except Exception as e:
        if conn:
            conn.rollback()
        results["error"] = f"An unexpected error occurred: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            
    return results


# -----------------------------------------
# 2. Helper Functions
# -----------------------------------------

def _get_available_faculty_for_session(cursor, exam_date, session):
    """
    Fetches all faculty who are marked as available for a given date and session.
    """
    query = """
        SELECT 
            f.id,
            f.faculty_id, 
            f.name, 
            f.designation, 
            f.department, 
            f.max_duties,
            (SELECT COUNT(*) FROM allocations WHERE faculty_id = f.id) as duties_assigned,
            GROUP_CONCAT(fs.course_code) AS subjects_handled
        FROM faculty f
        JOIN faculty_availability fa ON f.id = fa.faculty_id
        LEFT JOIN faculty_subjects fs ON f.id = fs.faculty_id
        WHERE 
            fa.availability_date = %s AND
            (fa.status = %s OR fa.status = 'Both') AND
            fa.status != 'Unavailable'
        GROUP BY f.id, f.faculty_id, f.name, f.designation, f.department, f.max_duties;
    """
    cursor.execute(query, (exam_date, session))
    return cursor.fetchall()


def _sort_by_designation_priority(faculty_list):
    """
    Sorts faculty based on designation.
    """
    priority = {
        "Assistant Professor": 1,
        "Associate Professor": 2,
        "Professor": 3
    }
    random.shuffle(faculty_list)
    faculty_list.sort(key=lambda x: priority.get(x['designation'], 99))


def _save_invigilation_duty(cursor, hall_id, faculty_db_id, exam_date, session):
    """
    Saves a single invigilation allocation record.
    """
    query = """
        INSERT INTO allocations (room_id, exam_id, faculty_id, allocation_date, session, status)
        VALUES (%s, NULL, %s, %s, %s, 'Confirmed');
    """
    cursor.execute(query, (hall_id, faculty_db_id, exam_date, session))

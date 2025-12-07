# faculty/faculty_availability.py
import mysql.connector
from database.db_connect import get_db_connection

def get_availability_by_faculty_id(faculty_id_from_session):
    """
    Fetches all availability records for a given faculty member.
    Args:
        faculty_id_from_session (str): The faculty_id from the session.
    Returns:
        list: A list of availability records (dictionaries), or an empty list if none are found or an error occurs.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # First, get the internal database ID from the faculty_id
        cursor.execute("SELECT id FROM faculty WHERE faculty_id = %s", (faculty_id_from_session,))
        faculty_db_id_row = cursor.fetchone()
        
        if not faculty_db_id_row:
            # This case should ideally not happen for a logged-in user
            return [], "Faculty not found."

        faculty_db_id = faculty_db_id_row['id']

        cursor.execute("""
            SELECT availability_id, availability_date, status
            FROM faculty_availability
            WHERE faculty_id = %s
            ORDER BY availability_date DESC
        """, (faculty_db_id,))
        
        return cursor.fetchall(), None
    except mysql.connector.Error as err:
        return [], f"Database error: {err}"
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def add_or_update_availability(faculty_id_from_session, availability_date, status):
    """
    Adds a new availability record or updates an existing one for a specific date.
    Args:
        faculty_id_from_session (str): The faculty_id from the session.
        availability_date (str): The date of the availability record (YYYY-MM-DD).
        status (str): The availability status (e.g., 'Available', 'Unavailable').
    Returns:
        dict: A message indicating success or failure.
        bool: True for success, False for failure.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the internal database ID from the faculty_id
        cursor.execute("SELECT id FROM faculty WHERE faculty_id = %s", (faculty_id_from_session,))
        faculty_db_id_row = cursor.fetchone()

        if not faculty_db_id_row:
            return {"message": "Error: Faculty ID not found."}, False

        faculty_db_id = faculty_db_id_row[0]

        # Use INSERT ... ON DUPLICATE KEY UPDATE to handle both new and existing records
        cursor.execute("""
            INSERT INTO faculty_availability (faculty_id, availability_date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """, (faculty_db_id, availability_date, status))
        
        conn.commit()
        
        if cursor.rowcount > 0:
            return {"message": "Availability updated successfully."}, True
        else:
            # This case might happen if the status submitted is the same as the one in the DB
            return {"message": "No changes made to availability."}, True

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        return {"message": f"Database error: {err}"}, False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

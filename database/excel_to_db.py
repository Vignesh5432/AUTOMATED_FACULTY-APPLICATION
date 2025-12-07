import pandas as pd
from db_connect import get_db_connection   # SQLite connection

# ✅ Excel File Name
excel_file = "database/faculty_data.xlsx"

# ✅ Read Excel
df = pd.read_excel(excel_file)

conn = get_db_connection()
cursor = conn.cursor()

for index, row in df.iterrows():
    faculty_name = str(row['Faculty_Name']).strip()
    dept = str(row['Dept']).strip()
    faculty_id_excel = str(row['Faculty_ID']).strip()
    designation = str(row['Designation']).strip()
    year_handling = str(row['Year Handling']).strip()
    availability = str(row['Availability']).strip()
    password = str(row['Password (Encrypted)\n']).strip()
    email = str(row['Email']).strip()

    # ✅ FIX: Normalize designation for SQLite CHECK constraint
    designation_map = {
        "hod": "HOD",
        "h.o.d": "HOD",
        "professor": "Professor",
        "assistant professor": "Assistant Professor",
        "asst prof": "Assistant Professor",
        "ap": "Assistant Professor"
    }

    designation_key = designation.lower()
    designation = designation_map.get(designation_key, "Assistant Professor")

    # ✅ Insert into USERS table (SQLite version)
    cursor.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email, password, "faculty")
    )

    user_id = cursor.lastrowid

    # ✅ Insert into FACULTY table
    cursor.execute(
        """
        INSERT INTO faculty 
        (user_id, faculty_name, department, designation, subjects_handled)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, faculty_name, dept, designation, year_handling)
    )

conn.commit()
cursor.close()
conn.close()

print("✅ Faculty Excel Data Uploaded Successfully!")

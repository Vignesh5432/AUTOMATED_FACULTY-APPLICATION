-- ✅ SQLITE DOES NOT USE CREATE DATABASE OR USE
-- The database is automatically created as the file: exam_management.db

-- ✅ USERS TABLE (For Login)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'faculty', 'student')) NOT NULL
);

-- ✅ FACULTY MASTER TABLE (From Your Excel)
CREATE TABLE IF NOT EXISTS faculty (
    faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    faculty_name TEXT,
    department TEXT,
    designation TEXT CHECK(designation IN ('HOD', 'Professor', 'Assistant Professor')),
    subjects_handled TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ✅ FACULTY AVAILABILITY
CREATE TABLE IF NOT EXISTS faculty_availability (
    availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER,
    exam_date DATE,
    is_available INTEGER DEFAULT 1,   -- 1 = TRUE, 0 = FALSE
    reason TEXT,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE
);

-- ✅ EXAMS TABLE (SEMESTER + INTERNALS)
CREATE TABLE IF NOT EXISTS exams (
    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT,
    exam_type TEXT CHECK(exam_type IN ('semester', 'internal')),
    exam_date DATE,
    session TEXT CHECK(session IN ('forenoon', 'afternoon', 'both'))
);

-- ✅ HALL ALLOCATION (FROM STUDENT TEAM)
CREATE TABLE IF NOT EXISTS hall_allocation (
    hall_id INTEGER PRIMARY KEY AUTOINCREMENT,
    hall_number TEXT,
    exam_id INTEGER,
    departments TEXT,
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
);

-- ✅ INVIGILATOR ALLOCATION
CREATE TABLE IF NOT EXISTS invigilator_allocation (
    allocation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER,
    hall_id INTEGER,
    exam_id INTEGER,
    duty_role TEXT CHECK(duty_role IN ('invigilator', 'squad')),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    FOREIGN KEY (hall_id) REFERENCES hall_allocation(hall_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

-- ✅ SUBSTITUTE FACULTY (EMERGENCY POOL)
CREATE TABLE IF NOT EXISTS substitute_faculty (
    substitute_id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER,
    exam_date DATE,
    is_used INTEGER DEFAULT 0,   -- 0 = FALSE, 1 = TRUE
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

-- ✅ REALLOCATION LOGS
CREATE TABLE IF NOT EXISTS reallocation_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    replaced_faculty_id INTEGER,
    substitute_faculty_id INTEGER,
    exam_id INTEGER,
    hall_id INTEGER,
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

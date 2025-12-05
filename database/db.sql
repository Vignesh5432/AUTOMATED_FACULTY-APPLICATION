-- ✅ CREATE DATABASE
CREATE DATABASE IF NOT EXISTS exam_management;
USE exam_management;

-- ✅ USERS TABLE (For Login)
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'faculty', 'student') NOT NULL
);

-- ✅ FACULTY MASTER TABLE (From Your Excel)
CREATE TABLE faculty (
    faculty_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    faculty_name VARCHAR(100),
    department VARCHAR(100),
    designation ENUM('HOD', 'Professor', 'Assistant Professor'),
    subjects_handled TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ✅ FACULTY AVAILABILITY
CREATE TABLE faculty_availability (
    availability_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT,
    exam_date DATE,
    is_available BOOLEAN DEFAULT TRUE,
    reason TEXT,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE
);

-- ✅ EXAMS TABLE (SEMESTER + INTERNALS)
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id VARCHAR(50),
    exam_type ENUM('semester', 'internal'),
    exam_date DATE,
    session ENUM('forenoon', 'afternoon', 'both')
);

-- ✅ HALL ALLOCATION (FROM STUDENT TEAM)
CREATE TABLE hall_allocation (
    hall_id INT AUTO_INCREMENT PRIMARY KEY,
    hall_number VARCHAR(50),
    exam_id INT,
    departments TEXT,
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
);

-- ✅ INVIGILATOR ALLOCATION
CREATE TABLE invigilator_allocation (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT,
    hall_id INT,
    exam_id INT,
    duty_role ENUM('invigilator', 'squad'),
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    FOREIGN KEY (hall_id) REFERENCES hall_allocation(hall_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

-- ✅ SUBSTITUTE FACULTY (EMERGENCY POOL)
CREATE TABLE substitute_faculty (
    substitute_id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT,
    exam_date DATE,
    is_used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id)
);

-- ✅ REALLOCATION LOGS
CREATE TABLE reallocation_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    replaced_faculty_id INT,
    substitute_faculty_id INT,
    exam_id INT,
    hall_id INT,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

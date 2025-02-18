import sqlite3
import hashlib

connection = sqlite3.connect("database.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS User (
    uid INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    dob DATE NOT NULL,
    role TEXT CHECK(role IN ('admin', 'user')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TRIGGER IF NOT EXISTS enforce_single_admin
BEFORE INSERT ON User
WHEN NEW.role = 'admin'
BEGIN
    SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM User WHERE role = 'admin') >= 1 THEN
            RAISE(ABORT, 'Only one admin is allowed in the system.')
    END;
END;
""")

cursor.execute("SELECT COUNT(*) FROM User WHERE role = 'admin'")
admin_count = cursor.fetchone()[0]
if admin_count == 0:
    cursor.execute("""
    INSERT OR IGNORE INTO User (uid, email, username, password, dob, role)
    VALUES (1, 'admin@a', 'Default Admin', ?, '01-01-25', 'admin');""",
                   (hashlib.sha256("x".encode()).hexdigest(),)
                   )

cursor.execute("""
CREATE TABLE IF NOT EXISTS Subject (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Chapter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES Subject (id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Quiz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chapter_id INTEGER NOT NULL,
    start_time DATETIME DEFAULT NULL,
    end_time DATETIME DEFAULT NULL,
    duration INTEGER DEFAULT NULL
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS QuizQuestion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    FOREIGN KEY (quiz_id) REFERENCES Quiz (id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES Question (id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Question (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL,
    question_statement TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT,
    option4 TEXT,
    correct_option INTEGER CHECK(correct_option BETWEEN 1 AND 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chapter_id) REFERENCES Chapter (id) ON DELETE CASCADE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS QuizAttempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(uid),
    FOREIGN KEY (quiz_id) REFERENCES Quiz(id)
);
""")

connection.commit()
connection.close()

print("Database and tables created successfully.")

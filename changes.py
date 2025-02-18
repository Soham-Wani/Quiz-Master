import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute(
    """CREATE TABLE IF NOT EXISTS QuizAttempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(uid),
    FOREIGN KEY (quiz_id) REFERENCES Quiz(id)
);
""")
conn.commit()
conn.close()
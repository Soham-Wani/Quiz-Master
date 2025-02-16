import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute(
    "ALTER TABLE Quiz ADD COLUMN chapter_id INTEGER NOT NULL DEFAULT 6;")
conn.commit()
conn.close()

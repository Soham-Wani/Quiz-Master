import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute(
    "ALTER TABLE Quiz ADD COLUMN duration INTEGER DEFAULT NULL;")
conn.commit()
conn.close()
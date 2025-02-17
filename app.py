import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = "your_secret_key"
DATABASE = "database.db"

logging.basicConfig(level=logging.DEBUG,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        action = request.form.get("action")

        try:
            conn = sqlite3.connect(DATABASE)
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()

            if action == "signin":
                email = request.form.get("email")
                password = hash_password(request.form.get("password"))

                cursor.execute(
                    "SELECT * FROM User WHERE email = ? AND password = ?", (email, password))
                user = cursor.fetchone()

                if user:
                    session["uid"] = user[0]
                    session["email"] = user[1]
                    session["role"] = user[5]

                    logging.info(
                        f"User '{email}' logged in successfully as '{user[5]}'.")

                    if session["role"] == "admin":
                        return redirect(url_for("admin_dashboard"))
                    else:
                        return redirect(url_for("user_dashboard"))

                else:
                    message = "Invalid credentials. Please try again."
                    logging.warning(
                        f"Failed login attempt for user '{email}'.")

            elif action == "signup":
                email = request.form.get("email")
                password = hash_password(request.form.get("password"))
                username = request.form.get("username")
                dob = request.form.get("dob")

                cursor.execute(
                    "INSERT INTO User (email, username, password, dob, role) VALUES (?, ?, ?, ?, 'user')",
                    (email, username, password, dob),
                )
                conn.commit()
                message = "Account created successfully! Please log in."
                logging.info(f"New user '{email}' signed up successfully.")

        except sqlite3.IntegrityError:
            message = "User already exists. Try logging in."
            logging.error(f"Signup failed: User '{email}' already exists.")

        except Exception as e:
            message = "An error occurred. Please try again."
            logging.exception(f"Unexpected error: {e}")

        finally:
            conn.close()

    return render_template("index.html", message=message)


@app.route("/dashboard/admin", methods=["GET", "POST"])
def admin_dashboard():
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON;")
    cursor = connection.cursor()

    if session.get("role") != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_subject":
            subject_name = request.form.get("subject_name")
            subject_description = request.form.get("subject_description")
            cursor.execute("INSERT INTO Subject (name, description) VALUES (?, ?)",
                           (subject_name, subject_description))
            connection.commit()

        elif action == "edit_subject":
            subject_id = request.form.get("subject_id")
            subject_name = request.form.get("subject_name")
            subject_description = request.form.get("subject_description")
            cursor.execute("UPDATE Subject SET name = ?, description = ? WHERE id = ?",
                           (subject_name, subject_description, subject_id))
            connection.commit()

        elif action == "delete_subject":
            subject_id = request.form.get("subject_id")
            cursor.execute("DELETE FROM Subject WHERE id = ?", (subject_id,))
            connection.commit()

        elif action == "add_chapter":
            subject_id = request.form.get("subject_id")
            chapter_name = request.form.get("chapter_name")
            chapter_description = request.form.get("chapter_description")
            cursor.execute("INSERT INTO Chapter (subject_id, name, description) VALUES (?, ?, ?)",
                           (subject_id, chapter_name, chapter_description))
            connection.commit()

        elif action == "edit_chapter":
            chapter_id = request.form.get("chapter_id")
            chapter_name = request.form.get("chapter_name")
            chapter_description = request.form.get("chapter_description")
            cursor.execute("UPDATE Chapter SET name = ?, description = ? WHERE id = ?",
                           (chapter_name, chapter_description, chapter_id))
            connection.commit()

        elif action == "delete_chapter":
            chapter_id = request.form.get("chapter_id")
            cursor.execute("DELETE FROM Chapter WHERE id = ?", (chapter_id,))
            connection.commit()

        elif action == "add_question":
            chapter_id = request.form.get("chapter_id")
            question_statement = request.form.get("question_statement")
            option1 = request.form.get("option1")
            option2 = request.form.get("option2")
            option3 = request.form.get("option3")
            option4 = request.form.get("option4")
            correct_option = request.form.get("correct_option")
            cursor.execute("""INSERT INTO Question
                              (chapter_id, question_statement, option1,
                               option2, option3, option4, correct_option)
                              VALUES (?, ?, ?, ?, ?, ?, ?)""",
                           (chapter_id, question_statement, option1, option2, option3, option4, correct_option))
            connection.commit()

        elif action == "edit_question":
            question_id = request.form.get("question_id")
            question_statement = request.form.get("question_statement")
            option1 = request.form.get("option1")
            option2 = request.form.get("option2")
            option3 = request.form.get("option3")
            option4 = request.form.get("option4")
            correct_option = request.form.get("correct_option")
            cursor.execute("""UPDATE Question
                              SET question_statement = ?, option1 = ?, option2 = ?, option3 = ?, option4 = ?, correct_option = ?
                              WHERE id = ?""",
                           (question_statement, option1, option2, option3, option4, correct_option, question_id))
            connection.commit()

        elif action == "delete_question":
            question_id = request.form.get("question_id")
            cursor.execute("DELETE FROM Question WHERE id = ?", (question_id,))
            connection.commit()

        # Create Quiz
        elif action == "create_quiz":
            quiz_title = request.form.get("quiz_title")
            quiz_description = request.form.get("quiz_description")
            chapter_id = request.form.get("selected_chapter")

            start_time = request.form.get("start_time") or None
            end_time = request.form.get("end_time") or None
            duration = request.form.get("duration") or None
            selected_questions = request.form.getlist("selected_questions")

            cursor.execute("""
                INSERT INTO Quiz (title, description, chapter_id, start_time, end_time, duration)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (quiz_title, quiz_description, chapter_id, start_time, end_time, duration))

            quiz_id = cursor.lastrowid  # Get new quiz ID

            # Insert selected questions into QuizQuestion table
            for question_id in selected_questions:
                cursor.execute(
                    "INSERT INTO QuizQuestion (quiz_id, question_id) VALUES (?, ?)", (quiz_id, question_id))

            connection.commit()

        elif action == "edit_quiz":
            quiz_id = request.form.get("quiz_id")
            quiz_title = request.form.get("quiz_title")
            quiz_description = request.form.get("quiz_description")
            selected_questions = request.form.getlist("selected_questions")
            start_time = request.form.get("start_time") or None
            end_time = request.form.get("end_time") or None
            duration = request.form.get("duration") or None

            cursor.execute("UPDATE Quiz SET title=?, description=?, start_time=?, end_time=?, duration=? WHERE id=?",
                           (quiz_title, quiz_description, start_time, end_time, duration, quiz_id))
            cursor.execute(
                "DELETE FROM QuizQuestion WHERE quiz_id=?", (quiz_id,))

            for question_id in selected_questions:
                cursor.execute(
                    "INSERT INTO QuizQuestion (quiz_id, question_id) VALUES (?, ?)", (quiz_id, question_id))
            connection.commit()

        elif action == "delete_quiz":
            quiz_id = request.form.get("quiz_id")
            cursor.execute(
                "DELETE FROM QuizQuestion WHERE quiz_id=?", (quiz_id,))
            cursor.execute("DELETE FROM Quiz WHERE id=?", (quiz_id,))
            connection.commit()

        return redirect(url_for("admin_dashboard"))

    search_query = request.args.get("search", "").strip()

    # Fetch Users
    if search_query:
        cursor.execute("SELECT * FROM User WHERE email LIKE ? OR username LIKE ?",
                       (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("SELECT * FROM User")
    users = cursor.fetchall()

    # Fetch Subjects
    if search_query:
        cursor.execute("SELECT * FROM Subject WHERE name LIKE ?",
                       (f"%{search_query}%",))
    else:
        cursor.execute("SELECT * FROM Subject")
    subjects = cursor.fetchall()

    # Fetch Quizzes
    if search_query:
        cursor.execute("SELECT * FROM Quiz WHERE title LIKE ?",
                       (f"%{search_query}%",))
    else:
        cursor.execute("SELECT * FROM Quiz")
    quizzes = cursor.fetchall()

    cursor.execute("SELECT * FROM Chapter")
    chapters = cursor.fetchall()

    cursor.execute("SELECT * FROM Question")
    questions = cursor.fetchall()

    cursor.execute("SELECT quiz_id, question_id FROM QuizQuestion")
    quiz_question_pairs = cursor.fetchall()

    subject_chapters = {sub[0]: [] for sub in subjects}
    for ch in chapters:
        if ch[1] in subject_chapters:
            subject_chapters[ch[1]].append(ch)
        else:
            print(f"Warning: Subject ID {ch[1]} not found in subjects!")

    chapter_questions = {ch[0]: [] for ch in chapters}
    for q in questions:
        if q[1] in chapter_questions:  # Check if the chapter exists before appending
            chapter_questions[q[1]].append(q)
        else:
            print(
                f"Warning: Chapter ID {q[1]} in questions not found in chapters!")

    quiz_questions = {}
    for quiz_id, question_id in quiz_question_pairs:
        if quiz_id not in quiz_questions:
            quiz_questions[quiz_id] = []
        quiz_questions[quiz_id].append(question_id)

    return render_template(
        "admin_dashboard.html",
        users=users,
        subjects=subjects,
        chapters=subject_chapters,
        questions=chapter_questions,
        quizzes=quizzes,
        quiz_questions=quiz_questions,
        search_query=search_query
    )


@app.route("/search", methods=["GET"])
def search():
    search_query = request.args.get("query", "").strip()

    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON;")
    cursor = connection.cursor()

    # Fetch Users
    cursor.execute("SELECT * FROM User WHERE email LIKE ? OR username LIKE ?",
                   (f"%{search_query}%", f"%{search_query}%"))
    users = cursor.fetchall()

    # Fetch Subjects
    cursor.execute("SELECT * FROM Subject WHERE name LIKE ?",
                   (f"%{search_query}%",))
    subjects = cursor.fetchall()

    # Fetch Quizzes
    cursor.execute("SELECT * FROM Quiz WHERE title LIKE ?",
                   (f"%{search_query}%",))
    quizzes = cursor.fetchall()

    connection.close()

    return jsonify({
        "users": users,
        "subjects": subjects,
        "quizzes": quizzes
    })


@app.route("/admin/summary_data")
def admin_summary_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Total Users Breakdown
    cursor.execute("SELECT COUNT(*) FROM User WHERE role='user'")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM User WHERE role='admin'")
    total_admins = cursor.fetchone()[0]

    # Subjects and Quizzes
    cursor.execute("SELECT COUNT(*) FROM Subject")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Quiz")
    total_quizzes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Question")
    total_questions = cursor.fetchone()[0]

    # User Registrations Over Time (last 7 days)
    cursor.execute("""
        SELECT strftime('%Y-%m-%d', dob) AS reg_date, COUNT(*) 
        FROM User 
        WHERE dob >= date('now', '-7 days') 
        GROUP BY reg_date
    """)
    user_registrations = cursor.fetchall()

    conn.close()

    return jsonify({
        "total_users": total_users,
        "total_admins": total_admins,
        "total_subjects": total_subjects,
        "total_quizzes": total_quizzes,
        "total_questions": total_questions,
        "user_registrations": user_registrations
    })


@app.route("/dashboard/user")
def user_dashboard():
    if "uid" in session and session.get("role") == "user":
        return render_template("user_dashboard.html")
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    if "email" in session:
        logging.info(f"User '{session['email']}' logged out.")
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

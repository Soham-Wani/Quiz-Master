import logging
from flask import Flask, render_template, request, redirect, url_for, session
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
    cursor = connection.cursor()
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add_subject":
            subject_name = request.form.get("subject_name")
            subject_description = request.form.get("subject_description")
            cursor.execute("INSERT INTO Subject (name, description) VALUES (?, ?)", (subject_name, subject_description))
            connection.commit()

        elif action == "add_chapter":
            subject_id = request.form.get("subject_id")
            chapter_name = request.form.get("chapter_name")
            chapter_description = request.form.get("chapter_description")
            cursor.execute("INSERT INTO Chapter (subject_id, name, description) VALUES (?, ?, ?)", 
                           (subject_id, chapter_name, chapter_description))
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
                              (chapter_id, question_statement, option1, option2, option3, option4, correct_option) 
                              VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                           (chapter_id, question_statement, option1, option2, option3, option4, correct_option))
            connection.commit()

        return redirect(url_for("admin_dashboard"))

    # Fetch subjects & their chapters
    cursor.execute("SELECT * FROM Subject")
    subjects = cursor.fetchall()

    cursor.execute("SELECT * FROM Chapter")
    chapters = cursor.fetchall()

    cursor.execute("SELECT * FROM Question")
    questions = cursor.fetchall()

    # Organize data
    subject_chapters = {sub[0]: [] for sub in subjects}
    for ch in chapters:
        subject_chapters[ch[1]].append(ch)

    chapter_questions = {ch[0]: [] for ch in chapters}
    for q in questions:
        chapter_questions[q[1]].append(q)

    return render_template("admin_dashboard.html", 
                           subjects=subjects, 
                           subject_chapters=subject_chapters, 
                           chapter_questions=chapter_questions)


@app.route("/dashboard/user")
def user_dashboard():
    if "uid" in session and session.get("role") == "user":
        return render_template("user_dashboard.html")
    return redirect(url_for("home"))


@app.route("/logout")
def logout():
    if "username" in session:
        logging.info(f"User '{session['email']}' logged out.")
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)


from flask import Flask, render_template, request, jsonify, flash, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "change-this-to-a-long-random-secret"

DATABASE = "assistant.db"


# 1. Database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# 2. Create database table
def create_table():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# 3. Home page and conversation history
@app.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    messages = conn.execute("""
        SELECT * FROM messages
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    return render_template("index.html", messages=messages)


# 4. Chat route
@app.route("/chat", methods=["POST"])
def chat():

    if "user_id" not in session:
        return jsonify({"error": "Please login first"}), 401

    data = request.get_json(silent=True) or {}

    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Temporary assistant response
    reply = "Hello! You said: " + user_message

    # Save conversation in database
    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO messages (user_message, assistant_response)
        VALUES (?, ?)
    """, (user_message, reply))

    message_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "id": message_id,
        "reply": reply
    })


# 5. Delete a conversation
@app.route("/delete/<int:message_id>", methods=["POST"])
def delete_message(message_id):

    conn = get_db()

    conn.execute(
        "DELETE FROM messages WHERE id = ?",
        (message_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({"success": True})


#login and register routes are not implemented yet.
from werkzeug.security import generate_password_hash, check_password_hash
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or len(password) < 8:
            flash("Enter all details. Password must have at least 8 characters.")
            return redirect("/register")

        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            """, (username, email, generate_password_hash(password)))

            conn.commit()

            flash("Registration successful! Please login.")
            return redirect("/login")

        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return redirect("/register")

        finally:
            conn.close()

    return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["username"] = user["username"]

            return redirect("/")

        flash("Invalid email or password.")

    return render_template("login.html")
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# 6. Start application
if __name__ == "__main__":
    create_table()
    app.run(debug=True)
import sys

path = '/home/endriasweb/ai-smart-assistant'

if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
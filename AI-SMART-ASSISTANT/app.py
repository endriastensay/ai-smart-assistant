import os
import sqlite3
import logging

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, flash
)

from dotenv import load_dotenv
from google import genai
from google.genai import types

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# ==========================================
# 1. CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "assistant.db")
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("FLASK_SECRET_KEY is missing from .env")

logging.basicConfig(level=logging.INFO)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
GEMINI_MODEL = "gemini-3.8-flash"

# ==========================================
# 2. DATABASE CONNECTION & INITIALIZATION
# ==========================================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL DEFAULT 'New conversation',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                conversation_id INTEGER,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

create_table()

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def login_required():
    return "user_id" in session

def get_user_conversation(conn, conversation_id):
    return conn.execute("""
        SELECT * FROM conversations WHERE id = ? AND user_id = ?
    """, (conversation_id, session["user_id"])).fetchone()

# ==========================================
# 4. GEMINI AI CONTROLLER
# ==========================================
def generate_ai_response(user_message, previous_messages):
    if client is None:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    conversation = []
    for message in previous_messages:
        conversation.append({"role": "user", "parts": [{"text": message["user_message"]}]})
        conversation.append({"role": "model", "parts": [{"text": message["assistant_response"]}]})

    conversation.append({"role": "user", "parts": [{"text": user_message}]})

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction="You are a friendly and intelligent AI Smart Assistant.",
            temperature=0.7,
            max_output_tokens=1500
        )
    )
    return response.text if response.text else "Empty response received."

# ==========================================
# 5. CORE ROUTING ENGINE
# ==========================================
@app.route("/")
def home():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    try:
        conversations = conn.execute(
            "SELECT * FROM conversations WHERE user_id = ? ORDER BY id DESC",
            (session["user_id"],)
        ).fetchall()

        conversation_id = request.args.get("conversation_id", type=int)
        selected = get_user_conversation(conn, conversation_id) if conversation_id else None

        if selected is None:
            if conversations:
                return redirect(url_for("home", conversation_id=conversations[0]["id"]))
            
            cursor = conn.execute(
                "INSERT INTO conversations (user_id, title) VALUES (?, ?)",
                (session["user_id"], "New conversation")
            )
            conn.commit()
            return redirect(url_for("home", conversation_id=cursor.lastrowid))

        messages = conn.execute("""
            SELECT * FROM messages WHERE user_id = ? AND conversation_id = ? ORDER BY id ASC
        """, (session["user_id"], selected["id"])).fetchall()

        theme = session.get("theme", "dark")
        return render_template(
            "index.html",
            conversations=conversations,
            messages=messages,
            active_conversation=selected,
            theme=theme
        )
    finally:
        conn.close()

@app.route("/chat", methods=["POST"])
def chat():
    if not login_required():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    conversation_id = data.get("conversation_id")

    if not user_message or not conversation_id:
        return jsonify({"error": "Missing message content or conversation ID"}), 400

    conn = get_db()
    try:
        selected_conv = get_user_conversation(conn, conversation_id)
        if not selected_conv:
            return jsonify({"error": "Conversation context missing"}), 404

        previous_messages = conn.execute("""
            SELECT user_message, assistant_response FROM messages 
            WHERE user_id = ? AND conversation_id = ? ORDER BY id ASC
        """, (session["user_id"], conversation_id)).fetchall()

        # Update title if it is a default conversation name
        if selected_conv["title"] == "New conversation":
            new_title = user_message[:25] + "..." if len(user_message) > 25 else user_message
            conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (new_title, conversation_id))

        ai_response = generate_ai_response(user_message, previous_messages)

        conn.execute("""
            INSERT INTO messages (user_id, conversation_id, user_message, assistant_response)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], conversation_id, user_message, ai_response))
        conn.commit()

        return jsonify({"reply": ai_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/new-chat", methods=["POST"])
def new_chat():
    if not login_required():
        return redirect(url_for("login"))
    
    conn = get_db()
    try:
        cursor = conn.execute("INSERT INTO conversations (user_id, title) VALUES (?, ?)", (session["user_id"], "New conversation"))
        conn.commit()
        return redirect(url_for("home", conversation_id=cursor.lastrowid))
    finally:
        conn.close()

@app.route("/delete-conversation/<int:conversation_id>", methods=["POST"])
def delete_conversation(conversation_id):
    if not login_required():
        return redirect(url_for("login"))
    
    conn = get_db()
    try:
        conn.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, session["user_id"]))
        conn.execute("DELETE FROM messages WHERE conversation_id = ? AND user_id = ?", (conversation_id, session["user_id"]))
        conn.commit()
    finally:
        conn.close()
    return redirect(url_for("home"))

# ==========================================
# 6. AUTHENTICATION (LOGIN/REGISTER/LOGOUT)
# ==========================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        
        hashed_password = generate_password_hash(password)
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
            conn.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.")
        finally:
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/toggle-theme", methods=["POST"])
def toggle_theme():
    data = request.get_json() or {}
    session["theme"] = data.get("theme", "dark")
    return jsonify({"status": "success"})

if __name__ == "__main__":
    app.run(debug=True)
def generate_ai_response(user_message, previous_messages):
    if client is None:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    conversation = []
    for message in previous_messages:
        conversation.append({"role": "user", "parts": [{"text": message["user_message"]}]})
        conversation.append({"role": "model", "parts": [{"text": message["assistant_response"]}]})

    conversation.append({"role": "user", "parts": [{"text": user_message}]})

    # Call the model via the new stable engine configuration
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=conversation,
        config=types.GenerateContentConfig(
            system_instruction="You are a friendly and intelligent AI Smart Assistant.",
            temperature=0.7,
            max_output_tokens=1500
        )
    )
    return response.text if response.text else "Empty response received."
import time
import logging

def generate_ai_response(user_message, previous_messages):
    if client is None:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    conversation = []
    for message in previous_messages:
        conversation.append({"role": "user", "parts": [{"text": message["user_message"]}]})
        conversation.append({"role": "model", "parts": [{"text": message["assistant_response"]}]})

    conversation.append({"role": "user", "parts": [{"text": user_message}]})

    # Resilience configuration: 3 structural reconnect attempts
    max_retries = 3
    retry_delay = 2  # Starting sleep threshold (in seconds)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=conversation,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "You are a friendly and intelligent AI Smart Assistant. "
                        "Answer naturally and clearly."
                    ),
                    temperature=0.7,
                    max_output_tokens=1500
                )
            )
            if response and response.text:
                return response.text
                
        except Exception as e:
            # Intercept service disruptions and scale out delay intervals
            if attempt < max_retries - 1:
                logging.warning(f"Google service busy (Attempt {attempt + 1}/{max_retries}). Retrying in {retry_delay}s... Details: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential progression (2s -> 4s)
                continue
            else:
                logging.error(f"Gemini interface dropped permanently after {max_retries} attempts: {e}")
                raise RuntimeError("The AI core service is currently processing high regional traffic. Please wait a brief moment and resubmit your prompt.")

    return "The assistant engine is experiencing high congestion rates. Please click send again."

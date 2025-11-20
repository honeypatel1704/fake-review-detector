from flask import (
    Flask, request, jsonify, render_template, redirect, url_for,
    session, g
)
from flask_cors import CORS
import joblib
import re
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

# -------------------------
# Configuration
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
MODEL_PATH = os.path.join(BASE_DIR, "custom_model.pkl")
VECT_PATH = os.path.join(BASE_DIR, "tfidf_vectorizer.pkl")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "replace_this_with_a_random_secret_in_production"  # change for production
CORS(app)

# -------------------------
# Load ML model & vectorizer
# -------------------------
try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECT_PATH)
except Exception as e:
    # If model files not found, raise helpful error
    raise RuntimeError(f"Could not load model/vectorizer: {e}")

# -------------------------
# Database helpers
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if they do not exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    # users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nickname TEXT,
            phone TEXT,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # predictions table: store review predictions (optional user_id)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            review TEXT,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# -------------------------
# Utility: login required decorator
# -------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------------
# Text cleaning function
# -------------------------
def clean_text(text):
    text = str(text or "")
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# -------------------------
# Context processor: make current_user available in templates
# -------------------------
@app.before_request
def load_logged_in_user():
    g.user = None
    if "user_id" in session:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, nickname FROM users WHERE id = ?", (session["user_id"],))
        row = cur.fetchone()
        conn.close()
        if row:
            g.user = {"id": row["id"], "username": row["username"], "nickname": row["nickname"]}

# -------------------------
# Routes - Frontend pages
# -------------------------
@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login_page():
    # GET -> show form
    if request.method == "GET":
        return render_template("login.html")

    # POST -> process login form
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return "<script>alert('Please provide username and password'); window.location='/login';</script>"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        # Successful login
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        return redirect(url_for("home_page"))
    else:
        return "<script>alert('Invalid username or password'); window.location='/login';</script>"

@app.route("/register", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html")

    # POST -> create user
    username = request.form.get("username", "").strip()
    nickname = request.form.get("nickname", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not username or not email or not password:
        return "<script>alert('Please fill required fields'); window.location='/register';</script>"

    if password != confirm:
        return "<script>alert('Passwords do not match'); window.location='/register';</script>"

    hashed = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, nickname, phone, email, password) VALUES (?, ?, ?, ?, ?)",
            (username, nickname, phone, email, hashed)
        )
        conn.commit()
        conn.close()
        return "<script>alert('Registration successful! Please login.'); window.location='/login';</script>"
    except sqlite3.IntegrityError as e:
        # likely username or email duplicate
        return f"<script>alert('Error: {str(e)}'); window.location='/register';</script>"
    except Exception as e:
        return f"<script>alert('Error: {str(e)}'); window.location='/register';</script>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home_page"))

@app.route("/predict_page")
def predict_page():
    return render_template("predict.html")

@app.route("/history")
@login_required
def history_page():
    # Show past predictions by logged-in user
    uid = session.get("user_id")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT review, result, created_at FROM predictions WHERE user_id = ? ORDER BY created_at DESC", (uid,))
    rows = cur.fetchall()
    conn.close()
    return render_template("history.html", predictions=rows)

@app.route("/team")
def team_page():
    return "<h1 style='padding:40px; font-family:Poppins;'>Team Page Coming Soon...</h1>"

@app.route("/contact")
def contact_page():
    return "<h1 style='padding:40px; font-family:Poppins;'>Contact Page Coming Soon...</h1>"

@app.route("/about")
def about_page():
    return "<h1 style='padding:40px; font-family:Poppins;'>About Us Page Coming Soon...</h1>"

# -------------------------
# API - prediction endpoint
# -------------------------
@app.route("/predict", methods=["POST"])
def predict():
    """
    Accepts JSON: { "review": "text here" }
    Returns JSON: { "prediction": "REAL" / "FAKE" }
    Also stores prediction into DB if user is logged in.
    """
    try:
        data = request.get_json(force=True)
        review = data.get("review", "")
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    if not isinstance(review, str) or review.strip() == "":
        return jsonify({"error": "Empty review"}), 400

    clean = clean_text(review)
    # vectorize + predict
    try:
        X = vectorizer.transform([clean])
        pred = model.predict(X)[0]
        result = "REAL" if int(pred) == 0 else "FAKE"
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    # store into DB (optional if logged in)
    userid = session.get("user_id")
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO predictions (user_id, review, result, created_at) VALUES (?, ?, ?, ?)",
            (userid, review, result, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception:
        # if DB insert fails, ignore but don't block response
        pass

    return jsonify({"prediction": result}), 200

# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    # ensure DB exists beforehand (already called above)
    app.run(host="0.0.0.0", port=5000)

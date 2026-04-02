from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# -------- DATABASE SETUP --------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS insurance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            premium REAL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# -------- PREMIUM LOGIC --------
def calculate_premium(age, smoker, health, term, ins_type):
    base = {"Life": 5000, "Health": 4000, "Vehicle": 3000}[ins_type]

    age_factor = 1.2 if age < 25 else 1.5 if age <= 40 else 2
    smoker_factor = 1.6 if smoker else 1
    health_factor = 1.4 if health else 1
    term_factor = 0.85 if term >= 10 else 0.9 if term >= 5 else 1

    premium = base * age_factor * smoker_factor * health_factor * term_factor

    if premium < 8000:
        risk = "Low Risk"
    elif premium < 15000:
        risk = "Medium Risk"
    else:
        risk = "High Risk"

    return premium, risk


# -------- REGISTER --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "Invalid credentials"

    return render_template("login.html")


# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# -------- MAIN PAGE --------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect("/login")

    premium = None
    risk = None

    if request.method == "POST":
        age = int(request.form["age"])
        term = int(request.form["term"])
        ins_type = request.form["type"]

        smoker = "smoker" in request.form
        health = "health" in request.form

        premium, risk = calculate_premium(age, smoker, health, term, ins_type)

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO insurance (premium) VALUES (?)", (premium,))
        conn.commit()
        conn.close()

    # -------- STATS --------
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT premium FROM insurance")
    data = [row[0] for row in c.fetchall()]
    conn.close()

    stats = None
    if data:
        stats = {
            "total": len(data),
            "avg": round(sum(data)/len(data), 2),
            "max": max(data),
            "min": min(data),
            "data": data
        }

    return render_template("index.html", premium=premium, risk=risk, stats=stats)


if __name__ == "__main__":
    app.run()
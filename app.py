import os
import functools
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Auth decorator                                                      #
# ------------------------------------------------------------------ #

def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name:
            error = "Name is required."
        elif "@" not in email or "." not in email:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            db = get_db()
            try:
                existing = db.execute(
                    "SELECT id FROM users WHERE email = ?", (email,)
                ).fetchone()
                if existing:
                    error = "Email already registered."
                else:
                    db.execute(
                        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                        (name, email, generate_password_hash(password)),
                    )
                    db.commit()
                    user = db.execute(
                        "SELECT id, name FROM users WHERE email = ?", (email,)
                    ).fetchone()
                    session["user_id"]   = user["id"]
                    session["user_name"] = user["name"]
                    return redirect(url_for("dashboard"))
            finally:
                db.close()

    return render_template("register.html", error=error)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Email and password are required."
        else:
            db = get_db()
            try:
                user = db.execute(
                    "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
                ).fetchone()
                if user is None or not check_password_hash(user["password_hash"], password):
                    error = "Invalid email or password."
                else:
                    session["user_id"]   = user["id"]
                    session["user_name"] = user["name"]
                    return redirect(url_for("dashboard"))
            finally:
                db.close()

    return render_template("login.html", error=error)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user = {
        "name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "joined": "January 2026",
    }
    stats = {
        "total_spent": "₹8,430.00",
        "transaction_count": 12,
        "top_category": "Food",
    }
    transactions = [
        {"date": "2026-05-05", "description": "Grocery run",       "category": "Food",          "amount": "₹320.00"},
        {"date": "2026-05-04", "description": "Metro pass top-up", "category": "Transport",     "amount": "₹85.50"},
        {"date": "2026-05-03", "description": "Electricity bill",  "category": "Bills",         "amount": "₹1,200.00"},
        {"date": "2026-05-02", "description": "Pharmacy",          "category": "Health",        "amount": "₹450.00"},
        {"date": "2026-05-01", "description": "Movie tickets",     "category": "Entertainment", "amount": "₹599.00"},
    ]
    breakdown = [
        {"category": "Food",          "amount": "₹2,840.00", "pct": 34},
        {"category": "Bills",         "amount": "₹2,400.00", "pct": 28},
        {"category": "Shopping",      "amount": "₹1,850.00", "pct": 22},
        {"category": "Transport",     "amount": "₹680.00",   "pct": 8},
        {"category": "Health",        "amount": "₹450.00",   "pct": 5},
        {"category": "Entertainment", "amount": "₹210.00",   "pct": 3},
    ]
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        breakdown=breakdown,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)

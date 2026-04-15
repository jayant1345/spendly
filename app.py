import os
import functools

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

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


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

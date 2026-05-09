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
            return redirect(url_for("login", next=request.path))
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
    uid = session["user_id"]
    db = get_db()
    try:
        user_row = db.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (uid,)
        ).fetchone()
        agg = db.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total "
            "FROM expenses WHERE user_id = ?", (uid,)
        ).fetchone()
        top_row = db.execute(
            "SELECT category FROM expenses WHERE user_id = ? "
            "GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1", (uid,)
        ).fetchone()
        expense_rows = db.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE user_id = ? ORDER BY date DESC", (uid,)
        ).fetchall()
        cat_rows = db.execute(
            "SELECT category, SUM(amount) as subtotal FROM expenses "
            "WHERE user_id = ? GROUP BY category ORDER BY subtotal DESC", (uid,)
        ).fetchall()
    finally:
        db.close()

    parts = user_row["name"].split()
    initials = "".join(p[0].upper() for p in parts[:2])

    def fmt_date(iso):
        try:
            return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y")
        except (ValueError, TypeError):
            return iso

    try:
        joined = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
    except (ValueError, TypeError):
        joined = user_row["created_at"]

    total = agg["total"]
    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "joined": joined,
        "initials": initials,
    }
    stats = {
        "total_spent": f"₹{total:,.2f}",
        "transaction_count": agg["cnt"],
        "top_category": top_row["category"] if top_row else "—",
    }
    expenses = [
        {
            "date": fmt_date(e["date"]),
            "description": e["description"] or "—",
            "category": e["category"],
            "amount": f"₹{e['amount']:,.2f}",
        }
        for e in expense_rows
    ]
    breakdown = []
    for c in cat_rows:
        pct = round(c["subtotal"] / total * 100) if total else 0
        breakdown.append({
            "category": c["category"],
            "amount": f"₹{c['subtotal']:,.2f}",
            "pct": pct,
        })

    return render_template(
        "dashboard.html",
        user=user, stats=stats,
        expenses=expenses, breakdown=breakdown,
    )


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
                    next_url = request.args.get("next", "")
                    if next_url and next_url.startswith("/"):
                        return redirect(next_url)
                    return redirect(url_for("dashboard"))
            finally:
                db.close()

    next_url = request.args.get("next", "")
    return render_template("login.html", error=error, next_url=next_url)


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
    return redirect(url_for("dashboard"))


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

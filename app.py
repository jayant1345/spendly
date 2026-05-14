import os
import re
import functools
from datetime import datetime, date, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, abort
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

CATEGORIES = [
    "Bills", "Education", "Entertainment",
    "Food", "Health", "Other", "Shopping", "Transport",
]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _valid_date(s):
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def _fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d %b %Y")
    except (ValueError, TypeError):
        return iso


def _first_day_n_months_ago(n, from_date):
    m, y = from_date.month - n, from_date.year
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def _validate_expense_form(raw_amount, category, expense_date, description):
    amount = None
    try:
        amount = float(raw_amount)
        if amount <= 0 or amount > 1_000_000:
            raise ValueError
    except (ValueError, TypeError):
        return None, "Amount must be a positive number."
    if category not in CATEGORIES:
        return None, "Please select a valid category."
    if not _valid_date(expense_date):
        return None, "Please enter a valid date."
    if len(description) > 200:
        return None, "Description must be 200 characters or fewer."
    return amount, None


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
    today = datetime.now()

    raw_from = request.args.get("date_from", "").strip()
    raw_to   = request.args.get("date_to",   "").strip()
    active_from = raw_from if _valid_date(raw_from) else ""
    active_to   = raw_to   if _valid_date(raw_to)   else ""

    if active_from and active_to and active_from > active_to:
        active_from, active_to = active_to, active_from

    default_from = today.replace(day=1).strftime("%Y-%m-%d")
    default_to   = today.strftime("%Y-%m-%d")

    clauses = ["user_id = ?"]
    params  = [uid]
    if active_from:
        clauses.append("date >= ?")
        params.append(active_from)
    if active_to:
        clauses.append("date <= ?")
        params.append(active_to)
    where = " AND ".join(clauses)

    db = get_db()
    try:
        user_row = db.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (uid,)
        ).fetchone()
        agg = db.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total "
            "FROM expenses WHERE " + where, params
        ).fetchone()
        top_row = db.execute(
            "SELECT category FROM expenses WHERE " + where +
            " GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1", params
        ).fetchone()
        expense_rows = db.execute(
            "SELECT id, date, description, category, amount FROM expenses "
            "WHERE " + where + " ORDER BY date DESC", params
        ).fetchall()
        cat_rows = db.execute(
            "SELECT category, SUM(amount) as subtotal FROM expenses "
            "WHERE " + where + " GROUP BY category ORDER BY subtotal DESC", params
        ).fetchall()
    finally:
        db.close()

    parts = user_row["name"].split()
    initials = "".join(p[0].upper() for p in parts[:2])

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
            "id": e["id"],
            "date": _fmt_date(e["date"]),
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

    td = today.date()
    first_this   = td.replace(day=1)
    last_m_start = _first_day_n_months_ago(1, first_this)
    last_m_end   = first_this - timedelta(days=1)

    presets = [
        {"label": "All time",      "date_from": "",                                                         "date_to": ""},
        {"label": "This month",    "date_from": first_this.strftime("%Y-%m-%d"),                             "date_to": td.strftime("%Y-%m-%d")},
        {"label": "Last month",    "date_from": last_m_start.strftime("%Y-%m-%d"),                          "date_to": last_m_end.strftime("%Y-%m-%d")},
        {"label": "Last 3 months", "date_from": _first_day_n_months_ago(3, first_this).strftime("%Y-%m-%d"), "date_to": td.strftime("%Y-%m-%d")},
        {"label": "Last 6 months", "date_from": _first_day_n_months_ago(6, first_this).strftime("%Y-%m-%d"), "date_to": td.strftime("%Y-%m-%d")},
    ]

    is_filtered = bool(active_from or active_to)
    return render_template(
        "dashboard.html",
        user=user, stats=stats,
        expenses=expenses, breakdown=breakdown,
        active_from=active_from, active_to=active_to,
        default_from=default_from, default_to=default_to,
        is_filtered=is_filtered, presets=presets,
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
    uid = session["user_id"]
    raw_month = request.args.get("month", "").strip()
    m = re.match(r'^(\d{4})-(\d{2})$', raw_month)
    active_month = raw_month if m and 1 <= int(m.group(2)) <= 12 else ""

    clauses = ["user_id = ?"]
    params  = [uid]
    if active_month:
        clauses.append("strftime('%Y-%m', date) = ?")
        params.append(active_month)
    where = " AND ".join(clauses)

    db = get_db()
    try:
        user_row = db.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (uid,)
        ).fetchone()
        agg = db.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total "
            "FROM expenses WHERE " + where, params
        ).fetchone()
        top_row = db.execute(
            "SELECT category FROM expenses WHERE " + where +
            " GROUP BY category ORDER BY COUNT(*) DESC LIMIT 1", params
        ).fetchone()
        expense_rows = db.execute(
            "SELECT date, description, category, amount FROM expenses "
            "WHERE " + where + " ORDER BY date DESC", params
        ).fetchall()
        cat_rows = db.execute(
            "SELECT category, SUM(amount) as subtotal FROM expenses "
            "WHERE " + where + " GROUP BY category ORDER BY subtotal DESC", params
        ).fetchall()
    finally:
        db.close()

    parts = user_row["name"].split()
    initials = "".join(p[0].upper() for p in parts[:2])

    try:
        joined = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y")
    except (ValueError, TypeError):
        joined = user_row["created_at"]

    display_month = ""
    if active_month:
        try:
            display_month = datetime.strptime(active_month, "%Y-%m").strftime("%B %Y")
        except ValueError:
            pass

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
    transactions = [
        {
            "date": _fmt_date(e["date"]),
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
        "profile.html",
        user=user, stats=stats,
        transactions=transactions, breakdown=breakdown,
        active_month=active_month, display_month=display_month,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    error = None
    today = datetime.now().strftime("%Y-%m-%d")
    form = {"amount": "", "category": "", "date": today, "description": ""}

    if request.method == "POST":
        raw_amount  = request.form.get("amount", "").strip()
        category    = request.form.get("category", "").strip()
        expense_date = request.form.get("date", "").strip()
        description  = request.form.get("description", "").strip()

        form = {"amount": raw_amount, "category": category,
                "date": expense_date, "description": description}

        amount, error = _validate_expense_form(raw_amount, category, expense_date, description)

        if not error:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO expenses (user_id, amount, category, date, description)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (session["user_id"], amount, category, expense_date, description),
                )
                db.commit()
            finally:
                db.close()
            return redirect(url_for("dashboard"))

    return render_template(
        "expense_form.html",
        error=error,
        categories=CATEGORIES,
        form=form,
        page_title="Add Expense",
        form_action=url_for("add_expense"),
        submit_label="Add Expense",
        subtitle="Record a new transaction to your account.",
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    db = get_db()
    try:
        expense = db.execute(
            "SELECT id, user_id, amount, category, date, description FROM expenses WHERE id = ?",
            (id,)
        ).fetchone()

        if expense is None:
            abort(404)
        if expense["user_id"] != session["user_id"]:
            abort(403)

        error = None
        form = {
            "amount": f"{expense['amount']:g}",
            "category": expense["category"],
            "date": expense["date"],
            "description": expense["description"] or "",
        }

        if request.method == "POST":
            raw_amount   = request.form.get("amount", "").strip()
            category     = request.form.get("category", "").strip()
            expense_date = request.form.get("date", "").strip()
            description  = request.form.get("description", "").strip()

            form = {"amount": raw_amount, "category": category,
                    "date": expense_date, "description": description}

            amount, error = _validate_expense_form(raw_amount, category, expense_date, description)

            if not error:
                db.execute(
                    "UPDATE expenses SET amount=?, category=?, date=?, description=?"
                    " WHERE id=? AND user_id=?",
                    (amount, category, expense_date, description,
                     id, session["user_id"]),
                )
                db.commit()
                return redirect(url_for("dashboard"))

    finally:
        db.close()

    return render_template(
        "expense_form.html",
        error=error,
        categories=CATEGORIES,
        form=form,
        page_title="Edit Expense",
        form_action=url_for("edit_expense", id=id),
        submit_label="Save Changes",
        subtitle="Update the details of this expense.",
    )


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true", port=5001)

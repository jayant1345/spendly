# CLAUDE.md — Spendly Expense Tracker

This file gives Claude Code context about the project so it can assist effectively.

## Project Overview

**Spendly** is a Flask web application for personal expense tracking. Users register, log expenses by category, and view monthly spending breakdowns on a dashboard.

## Stack

- **Backend:** Python 3, Flask
- **Database:** SQLite via `sqlite3` (file: `spendly.db`, git-ignored)
- **Auth:** Werkzeug `generate_password_hash` / `check_password_hash`, Flask `session`
- **Templates:** Jinja2 (`templates/`)
- **Styles:** Plain CSS (`static/css/style.css`) — no Tailwind, no Bootstrap
- **JS:** Vanilla JS (`static/js/main.js`) — no frameworks
- **Testing:** pytest + pytest-flask

## Project Structure

```
expense-tracker/
├── app.py                  # Flask app factory, all routes
├── database/
│   ├── __init__.py
│   └── db.py               # get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html           # Shared layout (navbar, footer)
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── dashboard.html      # Expense list + category breakdown
│   ├── expense_form.html   # Shared add / edit form
│   └── profile.html        # User profile + stats
├── static/
│   ├── css/style.css       # All styles (CSS variables at top)
│   └── js/main.js          # Client-side scripts
├── spendly.db              # SQLite DB — created at runtime, not in git
├── requirements.txt
├── README.md
└── CLAUDE.md               # This file
```

## Database Schema

```sql
users      (id, name, email, password_hash, created_at)
categories (id, name)                          -- seeded, not user-editable
expenses   (id, user_id, category_id, amount, description, date, created_at)
```

Foreign keys are enabled on every connection (`PRAGMA foreign_keys = ON`).
`get_db()` sets `row_factory = sqlite3.Row` so columns are accessible by name.

### Categories (fixed list)

Bills · Education · Entertainment · Food · Health · Other · Shopping · Transport

## Key Conventions

- All routes that require login use a `@login_required` decorator defined in `app.py`.
- The logged-in user's `id` and `name` are stored in `session["user_id"]` and `session["user_name"]`.
- Delete operations use `POST` (form button), not `GET`, to avoid accidental deletion via link.
- Amounts are stored as `REAL` in SQLite and displayed with `₹` prefix in templates.
- Dates are stored as `TEXT` in `YYYY-MM-DD` format.
- Month filters use `YYYY-MM` format passed as a `?month=` query parameter.

## CSS Design Tokens

All colours and fonts are CSS custom properties in `:root` at the top of `style.css`.
Key tokens:

| Variable          | Value     | Use                        |
|-------------------|-----------|----------------------------|
| `--ink`           | `#0f0f0f` | Primary text               |
| `--accent`        | `#1a472a` | Brand green, hover states  |
| `--accent-2`      | `#c17f24` | Secondary / warning        |
| `--danger`        | `#c0392b` | Delete actions             |
| `--paper`         | `#f7f6f3` | Page background            |
| `--font-display`  | DM Serif Display | Headings           |
| `--font-body`     | DM Sans   | Body text                  |

Do **not** use hardcoded hex values in new CSS — reference the variables instead.

## Running the App

```bash
# activate venv first
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

python app.py                  # runs on http://localhost:5001
```

`init_db()` is called automatically on startup.
To load sample data once: call `seed_db()` (creates `demo@example.com` / `password123`).

## Running Tests

```bash
pytest
```

## Environment Variables

| Variable     | Default                      | Notes                        |
|--------------|------------------------------|------------------------------|
| `SECRET_KEY` | `dev-secret-change-in-prod`  | Must be set in production    |

## What Claude Should Know

- The virtual environment is at `venv/` — do not modify it.
- `spendly.db` is runtime-generated — never commit it.
- All new routes should follow the existing pattern: decorator → validate → db → redirect/render.
- Form validation is done server-side in the route; templates display an `{{ error }}` variable.
- The `base.html` navbar conditionally renders auth vs. logged-in links using `session.get('user_id')`.
- Prefer editing existing files over creating new ones.
- Keep JS minimal — this is a server-rendered app, not a SPA.

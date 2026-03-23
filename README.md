# Spendly — Personal Expense Tracker

A Flask web application to log expenses, understand spending patterns, and take control of your financial life.

## Features

- **User authentication** — register, login, logout with hashed passwords
- **Expense logging** — add, edit, and delete expenses with category, amount, date, and description
- **Dashboard** — monthly overview with category breakdown and spending totals
- **Profile page** — view account info and lifetime spending stats
- **Filter by month** — view expenses for any month at a glance

## Tech Stack

| Layer     | Technology                  |
|-----------|-----------------------------|
| Backend   | Python 3, Flask             |
| Database  | SQLite (via `sqlite3`)      |
| Auth      | Werkzeug password hashing   |
| Frontend  | Jinja2 templates, plain CSS |
| Testing   | pytest, pytest-flask        |

## Project Structure

```
expense-tracker/
├── app.py                  # Flask app, routes
├── database/
│   ├── __init__.py
│   └── db.py               # get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html           # Shared layout
│   ├── landing.html        # Public landing page
│   ├── login.html          # Login form
│   ├── register.html       # Registration form
│   ├── dashboard.html      # Expense dashboard (auth required)
│   ├── expense_form.html   # Add / edit expense form
│   └── profile.html        # User profile
├── static/
│   ├── css/style.css       # All styles
│   └── js/main.js          # Client-side scripts
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd expense-tracker
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

The app will be available at `http://localhost:5001`.

## Database

The SQLite database (`spendly.db`) is created automatically on first run via `init_db()`.

To load sample data for development, call `seed_db()` once:

```python
from database.db import seed_db
seed_db()
```

This creates a demo account:

| Field    | Value               |
|----------|---------------------|
| Email    | demo@example.com    |
| Password | password123         |

## Running Tests

```bash
pytest
```

## Expense Categories

Bills · Education · Entertainment · Food · Health · Other · Shopping · Transport

## Environment Variables

| Variable     | Default                    | Description              |
|--------------|----------------------------|--------------------------|
| `SECRET_KEY` | `dev-secret-change-in-prod`| Flask session secret key |

Set a strong `SECRET_KEY` in production:

```bash
export SECRET_KEY="your-random-secret-here"
```

## License

MIT

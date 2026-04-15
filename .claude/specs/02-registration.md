# Spec: Registration

## Overview
Implement user registration so a visitor can create a Spendly account by submitting their
name, email address, and password. On success the user is immediately signed in (session
created) and redirected to a dashboard placeholder. This step also wires up Flask sessions
(SECRET_KEY) and updates the shared navbar in `base.html` to show context-aware links
depending on whether a user is logged in.

## Depends on
- Step 01 — Database Setup (users table must exist)

## Routes
- `GET  /register` — render registration form — public (already exists as stub, keep GET)
- `POST /register` — validate form, insert user, set session, redirect — public
- `GET  /dashboard` — placeholder landing page for authenticated users — logged-in

The existing GET /register stub in `app.py` must be updated to accept both methods.
The /dashboard route is added as a minimal placeholder (a full dashboard comes in a later step).

## Database changes
No new tables or columns. The existing `users` table (id, name, email, password_hash,
created_at) is sufficient.

## Templates
- **Modify:** `templates/register.html` — no structural changes needed; the form already
  POSTs to `/register` and displays `{{ error }}`. No edits required unless testing reveals
  a gap.
- **Modify:** `templates/base.html` — update the `<nav>` links to conditionally render:
  - When **not** logged in: show "Sign in" and "Get started" (current behaviour)
  - When **logged in**: show "Dashboard" and "Sign out" links instead
- **Create:** `templates/dashboard.html` — minimal placeholder that extends `base.html`;
  displays a heading ("Your Dashboard") and a brief "coming soon" note. Will be replaced
  fully in a later step.

## Files to change
- `app.py` — add SECRET_KEY, update `/register` to handle POST, add `/dashboard` route,
  add `login_required` decorator
- `templates/base.html` — conditional nav links based on `session.get('user_id')`

## Files to create
- `templates/dashboard.html` — minimal placeholder

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Use CSS variables — never hardcode hex values in new CSS
- All templates extend `base.html`
- `SECRET_KEY` must be set on the Flask app before sessions will work; use
  `os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")`
- The `login_required` decorator must redirect to `/login` if `session.get('user_id')` is falsy
- Server-side validation must reject: empty name, empty/invalid email, password shorter
  than 8 characters, and an email already present in the users table
- After a successful registration set **both** `session["user_id"]` and `session["user_name"]`
- Use `redirect(url_for('dashboard'))` after successful registration
- The `/register` GET handler must redirect to `/dashboard` if the user is already logged in
- Close every `get_db()` connection in a `finally` block (or use try/finally)

## Definition of done
- [ ] Visiting `/register` while logged out shows the registration form
- [ ] Visiting `/register` while logged in redirects to `/dashboard`
- [ ] Submitting the form with an empty name shows an inline error message
- [ ] Submitting the form with an invalid email shows an inline error message
- [ ] Submitting a password shorter than 8 characters shows an inline error message
- [ ] Submitting a duplicate email shows an inline error message ("Email already registered")
- [ ] Submitting valid details creates a row in the `users` table with a hashed password
- [ ] After successful registration the browser is redirected to `/dashboard`
- [ ] `/dashboard` is accessible only when logged in; visiting it logged-out redirects to `/login`
- [ ] The navbar shows "Dashboard" and "Sign out" after registration (not "Sign in" / "Get started")
- [ ] The app starts without errors (`python app.py`)

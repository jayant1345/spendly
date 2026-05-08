# Spec: Login and Logout

## Overview
Implement fully functional login and logout for Spendly. A returning user can sign in with
their email and password, land on the dashboard, and sign out to end their session. The
`/login` route already has a working stub in `app.py`; this step verifies it and completes
the one missing piece: logout must use POST (not GET) so a stray link or prefetch cannot
silently end a user's session. The navbar's "Sign out" link must be converted to a small
inline form that POSTs to `/logout`.

## Depends on
- Step 01 — Database Setup (users table and get_db must work)
- Step 02 — Registration (session keys user_id / user_name must be set on login)

## Routes
- `GET  /login`  — render login form; redirect to /dashboard if already logged in — public
- `POST /login`  — validate credentials, set session, redirect to /dashboard — public
- `POST /logout` — clear session, redirect to /landing — logged-in (change from GET to POST)

## Database changes
No database changes. The `users` table (id, name, email, password_hash) already has
everything needed.

## Templates
- **Modify:** `templates/base.html` — replace the `<a href="/logout">` nav link with a
  `<form method="POST" action="/logout">` containing a single submit button styled to look
  like a link. This is the only structural change needed.
- **Verify (no edits expected):** `templates/login.html` — the form POSTs to `/login` and
  displays `{{ error }}`; confirm it renders correctly end-to-end.

## Files to change
- `app.py` — change `/logout` route from `GET` to `POST`; keep the rest of the login/logout
  logic as-is (it is already correct)
- `templates/base.html` — replace logout anchor tag with a POST form
- `static/css/style.css` — add `.btn-logout` style so the form button looks like a nav link
  (no background, no border, cursor pointer, inherits font and colour from nav)

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords verified with `werkzeug.security.check_password_hash`
- Use CSS variables — never hardcode hex values in new CSS
- All templates extend `base.html`
- Logout **must** be `POST`. Do not revert to GET.
- The logout form in the navbar must not break the existing nav layout — keep it inline
- The `@login_required` decorator already exists; do not duplicate it
- Close every `get_db()` connection in a `finally` block (already the pattern in app.py)
- `/login` GET must redirect to `/dashboard` if `session.get('user_id')` is truthy

## Definition of done
- [ ] Visiting `/login` while logged out renders the sign-in form
- [ ] Visiting `/login` while already logged in redirects to `/dashboard`
- [ ] Submitting `/login` with empty email or password shows inline error "Email and password are required."
- [ ] Submitting `/login` with a wrong password shows inline error "Invalid email or password."
- [ ] Submitting `/login` with a wrong email shows inline error "Invalid email or password."
- [ ] Submitting `/login` with valid credentials sets `session["user_id"]` and `session["user_name"]` and redirects to `/dashboard`
- [ ] After login the navbar shows "Dashboard" and "Sign out" (not "Sign in" / "Get started")
- [ ] Clicking "Sign out" sends a POST to `/logout` (verify in browser DevTools Network tab)
- [ ] After logout `session["user_id"]` is cleared; visiting `/dashboard` redirects to `/login`
- [ ] After logout the navbar shows "Sign in" and "Get started"
- [ ] A direct GET request to `/logout` returns 405 Method Not Allowed (not a silent redirect)
- [ ] The "Sign out" button in the navbar looks visually consistent with the surrounding nav links
- [ ] The app starts without errors (`python app.py`)

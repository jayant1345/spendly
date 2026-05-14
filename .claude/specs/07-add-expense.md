# Spec: Add Expense

## Overview
This feature replaces the `/expenses/add` stub route with a fully functional form that lets logged-in users record a new expense. The user fills in an amount, category, date, and optional description, then submits. A valid submission inserts a row into the `expenses` table and redirects to the dashboard. This is the first write-path feature beyond registration, and it establishes the `expense_form.html` template that the later edit step will reuse.

## Depends on
- Step 01: Database setup (`expenses` table must exist)
- Step 02: Registration (user accounts must exist)
- Step 03: Login and Logout (session + `@login_required` decorator in place)

## Routes
- `GET /expenses/add` — render the blank add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the expense, redirect to `/dashboard` on success — logged-in only

## Database changes
No database changes. The existing `expenses` table `(id, user_id, amount, category, date, description, created_at)` is sufficient.

## Templates
- **Create:** `templates/expense_form.html`
  - Extends `base.html`
  - Contains a `<form method="POST" action="/expenses/add">`
  - Fields:
    - `amount` — `<input type="number" step="0.01" min="0.01" name="amount">` — required
    - `category` — `<select name="category">` — required; options are the eight fixed categories: Bills, Education, Entertainment, Food, Health, Other, Shopping, Transport
    - `date` — `<input type="date" name="date">` — required; pre-filled with today's date
    - `description` — `<input type="text" name="description">` — optional, max 200 chars
  - Displays `{{ error }}` when validation fails
  - Submit button labelled "Add Expense"

## Files to change
- `app.py` — replace the two-line `/expenses/add` stub with a real view function:
  - Decorate with `@login_required`
  - Accept `GET` and `POST` methods
  - On GET: render `expense_form.html` with `date` pre-filled to `datetime.now().strftime("%Y-%m-%d")`
  - On POST:
    - Read `amount`, `category`, `date`, `description` from `request.form`
    - Validate: `amount` must be a positive number; `category` must be one of the eight fixed values; `date` must pass `_valid_date()`
    - On failure: re-render `expense_form.html` with `error` and the submitted values so the user doesn't lose their input
    - On success: insert into `expenses` using a parameterised query, commit, close db, redirect to `/dashboard`

## Files to create
- `templates/expense_form.html` — the add/edit shared form template (add-only for this step)

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Category validation: check submitted value against the fixed list server-side; do not trust client input alone
- Amount validation: use `float()` in a try/except; reject zero and negative values
- Date validation: use the existing `_valid_date()` helper
- Description is optional — store `None` if blank; do not store an empty string
- The form `action` must be `/expenses/add` for the add route (not a dynamic path)
- On success, redirect to `url_for("dashboard")` — do not render a template
- Delete the two placeholder routes for `/expenses/<int:id>/edit` and `/expenses/<int:id>/delete` if they break the app, otherwise leave them as stubs

## Definition of done
- [ ] Visiting `/expenses/add` without being logged in redirects to `/login`
- [ ] Visiting `GET /expenses/add` while logged in returns HTTP 200 and renders a form with amount, category, date, and description fields
- [ ] The date field is pre-filled with today's date
- [ ] The category dropdown contains all eight fixed categories
- [ ] Submitting the form with valid data inserts a row into the `expenses` table and redirects to `/dashboard`
- [ ] The new expense appears on the dashboard immediately after redirect
- [ ] Submitting with a missing or zero amount shows an error message and keeps the other field values
- [ ] Submitting with an invalid date shows an error message
- [ ] Submitting with a category not in the fixed list shows an error message
- [ ] Description is optional — submitting without it succeeds and stores `NULL` in the database
- [ ] A description longer than 200 characters is rejected with an error message

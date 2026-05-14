# Spec: Edit Expense

## Overview
This feature replaces the `/expenses/<id>/edit` stub with a fully functional edit flow. A logged-in user can click an "Edit" button next to any of their own expenses on the dashboard, land on a pre-filled form, change any field, and save the update. The `expense_form.html` template from Step 07 is made reusable by parameterising its title, form action, and submit label — the add route is updated to pass those same variables so behaviour is unchanged. Ownership is enforced server-side: a user cannot edit another user's expense.

## Depends on
- Step 01: Database setup (`expenses` table must exist)
- Step 02: Registration (user accounts must exist)
- Step 03: Login and Logout (session + `@login_required` decorator)
- Step 07: Add Expense (`expense_form.html` template created)

## Routes
- `GET /expenses/<int:id>/edit` — fetch the expense, verify ownership, render pre-filled form — logged-in only
- `POST /expenses/<int:id>/edit` — validate submitted data, update the row, redirect to dashboard — logged-in only

## Database changes
No database changes. The existing `expenses` table is sufficient.

## Templates
- **Modify:** `templates/expense_form.html`
  - Replace hardcoded heading "Add Expense" with `{{ page_title }}`
  - Replace hardcoded `action="{{ url_for('add_expense') }}"` with `action="{{ form_action }}"`
  - Replace hardcoded button label "Add Expense" with `{{ submit_label }}`
  - No other structural changes — the four form fields stay identical

- **Modify:** `templates/dashboard.html`
  - Add `id` to the `SELECT` in the dashboard query (via `app.py` change)
  - Add an "Edit" link column to the expense table header and each row: `<a href="{{ url_for('edit_expense', id=e.id) }}">Edit</a>`
  - Style the edit link with existing CSS patterns (no new classes required unless the design calls for it)

## Files to change
- `app.py`
  - **`dashboard` route:** add `id` to the `SELECT` and include `"id": e["id"]` in the expense dict passed to the template
  - **`add_expense` route:** pass three new template variables — `page_title="Add Expense"`, `form_action=url_for('add_expense')`, `submit_label="Add Expense"` — on both GET and POST renders
  - **`edit_expense` route:** replace the one-line stub with a full implementation:
    - Add `@login_required` decorator
    - Accept `methods=["GET", "POST"]`
    - On both GET and POST: fetch the expense by `id`; if not found, abort(404); if `expense["user_id"] != session["user_id"]`, abort(403)
    - On GET: render `expense_form.html` with `page_title`, `form_action`, `submit_label`, `categories`, and `form` pre-filled from the fetched row
    - On POST: validate identically to `add_expense`; on success, run `UPDATE expenses SET amount=?, category=?, date=?, description=? WHERE id=? AND user_id=?`; commit, close db, redirect to `url_for("dashboard")`; on failure, re-render with `error` and submitted values

- `templates/expense_form.html` — make title, action, and submit label dynamic (see Templates section)
- `templates/dashboard.html` — add Edit link column to the expense table

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never string-format SQL
- Passwords hashed with werkzeug (no auth changes in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Ownership check is mandatory: always verify `expense["user_id"] == session["user_id"]` before serving or saving; use `abort(403)` if it fails
- The `WHERE id=? AND user_id=?` clause in the UPDATE is a second layer of ownership protection — always include it
- Validation rules for the edit POST are identical to add: amount must be a positive number ≤ 1,000,000; category must be in `CATEGORIES`; date must pass `_valid_date()`; description max 200 chars
- On validation failure, re-render the form with the submitted values (not the original DB values) so the user sees their own input
- The add route must pass `page_title`, `form_action`, and `submit_label` so the template still works for adding after the template change
- Do not add a separate "actions" column to the dashboard table if it breaks the existing layout — place the edit link inline within an existing cell or as a minimal extra column

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` without being logged in redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for a non-existent expense returns 404
- [ ] Visiting `/expenses/<id>/edit` for another user's expense returns 403
- [ ] `GET /expenses/<id>/edit` returns 200 and renders the form with all four fields pre-filled from the database row
- [ ] The category dropdown has the correct category pre-selected
- [ ] `POST /expenses/<id>/edit` with valid data updates the row in `expenses` and redirects to `/dashboard`
- [ ] The updated values appear immediately on the dashboard after redirect
- [ ] `POST /expenses/<id>/edit` with a missing or zero amount shows an error and keeps submitted values
- [ ] `POST /expenses/<id>/edit` with an invalid date shows an error
- [ ] `POST /expenses/<id>/edit` with a category not in the fixed list shows an error
- [ ] A description longer than 200 characters is rejected with an error
- [ ] The dashboard expense table shows an "Edit" link for each expense
- [ ] The "Add Expense" form still works correctly after the template changes

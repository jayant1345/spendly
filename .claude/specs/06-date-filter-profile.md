# Spec: Date Filter for Profile Page

## Overview
This feature replaces the `/profile` stub route with a fully functional profile page backed by real database queries, and adds a month-based date filter so users can narrow their transaction history and spending stats to a specific month. The filter uses the `?month=YYYY-MM` query parameter — consistent with how filtering is documented in `CLAUDE.md`. When no month is provided, the page shows all-time data. This step wires up the profile page to real data (completing what was left open after Step 04) and introduces the first client-visible filter interaction in the app.

## Depends on
- Step 01: Database setup (schema must exist)
- Step 02: Registration (user accounts must exist)
- Step 03: Login and Logout (session management in place)
- Step 04: Profile Page Creation (`profile.html` template must exist with the expected variable slots)

## Routes
- `GET /profile` — renders the profile page with real DB data; supports optional `?month=YYYY-MM` query parameter — logged-in only

## Database changes
No database changes. The existing `users` and `expenses` tables are sufficient. All filtering is done at query time using SQL `WHERE` clauses with the `strftime` function on the `date` column.

## Templates
- **Modify:** `templates/profile.html`
  - Add a month filter control above the Recent Transactions section: a `<form method="GET" action="/profile">` containing a `<input type="month" name="month">` pre-filled with the active month, plus a Submit button and a "Clear" link back to `/profile`
  - When a month filter is active, display the selected month label (e.g. "April 2026") as a visible heading or subtitle near the stats and transactions sections
  - The stats row (Total Spent, Transactions, Top Category) must reflect the filtered period, not all-time totals

## Files to change
- `app.py` — replace the `/profile` redirect stub with a real view function that:
  - Reads `request.args.get("month", "")` and validates it matches `YYYY-MM` format (reject anything else silently by treating it as no filter)
  - Queries `users` for name, email, created_at
  - Queries `expenses` filtered by `user_id` and, when a month is given, by `strftime('%Y-%m', date) = ?`
  - Computes: total spent, transaction count, top category, per-category breakdown with percentages
  - Passes `user`, `stats`, `transactions`, `breakdown`, and `active_month` to `profile.html`
- `templates/profile.html` — add the month filter form and conditional month label (see Templates section above)

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
- Month validation: if `?month=` is present but does not match `^\d{4}-\d{2}$`, treat it as absent (no error shown, no crash)
- When no month filter is active, `active_month` passed to the template must be `""` (empty string), not `None`
- SQL filter clause: `strftime('%Y-%m', date) = ?` — do not use `LIKE` or string slicing
- The filter form must use `GET`, not `POST`, so the filtered URL is bookmarkable
- Category breakdown percentages must be computed relative to the filtered total, not the all-time total

## Definition of done
- [ ] Visiting `/profile` without being logged in redirects to `/login`
- [ ] Visiting `/profile` while logged in returns HTTP 200 and shows the user's real name and email from the database
- [ ] The stats row shows real totals computed from the `expenses` table for that user
- [ ] The Recent Transactions table shows real rows from the database ordered by date descending
- [ ] A month filter `<input type="month">` is visible on the page
- [ ] Submitting the filter with a valid month (e.g. `2026-04`) reloads the page with `?month=2026-04` in the URL
- [ ] When `?month=2026-04` is active, only transactions from April 2026 appear in the table
- [ ] When `?month=2026-04` is active, the stats row reflects April 2026 totals only
- [ ] The "Clear" link removes the filter and shows all-time data
- [ ] A month with no expenses shows zero totals and an empty-state message in the transactions table
- [ ] An invalid `?month=` value (e.g. `?month=bad`) does not crash the app — it falls back to all-time view

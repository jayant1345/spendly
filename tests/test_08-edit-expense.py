"""
Tests for the Edit Expense feature (Spec 08).

Tests validate the /expenses/<id>/edit route functionality for both GET and POST
operations, covering all validation rules, ownership checks, and integration
with the dashboard from the spec's Definition of Done checklist.
"""
import pytest
from database.db import get_db
from werkzeug.security import generate_password_hash


@pytest.fixture
def second_user():
    """Create a second test user to test ownership checks."""
    from database.db import get_db

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Jane Smith", "jane@example.com", generate_password_hash("password456"))
        )
        user_id = cursor.lastrowid
        db.commit()
        return {
            'id': user_id,
            'name': "Jane Smith",
            'email': "jane@example.com"
        }
    finally:
        db.close()


@pytest.fixture
def test_expense(test_user):
    """Create a test expense owned by the primary test user."""
    from database.db import get_db

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (test_user['id'], 150.75, "Food", "2026-05-10", "Restaurant dinner")
        )
        expense_id = cursor.lastrowid
        db.commit()
        return {
            'id': expense_id,
            'user_id': test_user['id'],
            'amount': 150.75,
            'category': "Food",
            'date': "2026-05-10",
            'description': "Restaurant dinner"
        }
    finally:
        db.close()


@pytest.fixture
def other_users_expense(second_user):
    """Create a test expense owned by the second user."""
    from database.db import get_db

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (second_user['id'], 75.50, "Transport", "2026-05-12", "Metro ticket")
        )
        expense_id = cursor.lastrowid
        db.commit()
        return {
            'id': expense_id,
            'user_id': second_user['id'],
            'amount': 75.50,
            'category': "Transport",
            'date': "2026-05-12",
            'description': "Metro ticket"
        }
    finally:
        db.close()


class TestEditExpenseAuthentication:
    """Test authentication requirements for edit expense functionality."""

    def test_edit_expense_unauthenticated_redirects_to_login(self, client, test_expense):
        """Test that visiting /expenses/<id>/edit without login redirects to /login."""
        response = client.get(f'/expenses/{test_expense["id"]}/edit')
        assert response.status_code == 302
        assert '/login' in response.headers['Location']

    def test_edit_expense_post_unauthenticated_redirects_to_login(self, client, test_expense):
        """Test that POST to /expenses/<id>/edit without login redirects to /login."""
        response = client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '200.00',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated expense'
        })
        assert response.status_code == 302
        assert '/login' in response.headers['Location']


class TestEditExpenseNotFound:
    """Test handling of non-existent expense IDs."""

    def test_edit_expense_nonexistent_id_returns_404(self, authenticated_client, test_user):
        """Test that GET /expenses/9999/edit for non-existent ID returns 404."""
        response = authenticated_client.get('/expenses/9999/edit')
        assert response.status_code == 404

    def test_edit_expense_post_nonexistent_id_returns_404(self, authenticated_client, test_user):
        """Test that POST /expenses/9999/edit for non-existent ID returns 404."""
        response = authenticated_client.post('/expenses/9999/edit', data={
            'amount': '200.00',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated expense'
        })
        assert response.status_code == 404


class TestEditExpenseOwnership:
    """Test ownership enforcement for edit expense functionality."""

    def test_edit_expense_other_users_expense_returns_403(self, authenticated_client, test_user, other_users_expense):
        """Test that GET /expenses/<id>/edit for another user's expense returns 403."""
        response = authenticated_client.get(f'/expenses/{other_users_expense["id"]}/edit')
        assert response.status_code == 403

    def test_edit_expense_post_other_users_expense_returns_403(self, authenticated_client, test_user, other_users_expense):
        """Test that POST /expenses/<id>/edit for another user's expense returns 403."""
        response = authenticated_client.post(f'/expenses/{other_users_expense["id"]}/edit', data={
            'amount': '200.00',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated expense'
        })
        assert response.status_code == 403


class TestEditExpenseGetForm:
    """Test GET /expenses/<id>/edit form rendering and pre-filling."""

    def test_edit_expense_get_returns_200_with_form(self, authenticated_client, test_user, test_expense):
        """Test that GET /expenses/<id>/edit for owner returns 200 with form."""
        response = authenticated_client.get(f'/expenses/{test_expense["id"]}/edit')
        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'Edit Expense' in response_text

    def test_edit_expense_form_prefilled_amount(self, authenticated_client, test_user, test_expense):
        """Test that the amount field is pre-filled with current value."""
        response = authenticated_client.get(f'/expenses/{test_expense["id"]}/edit')
        response_text = response.data.decode()
        assert f'value="150.75"' in response_text

    def test_edit_expense_form_prefilled_date(self, authenticated_client, test_user, test_expense):
        """Test that the date field is pre-filled with current value."""
        response = authenticated_client.get(f'/expenses/{test_expense["id"]}/edit')
        response_text = response.data.decode()
        assert f'value="2026-05-10"' in response_text

    def test_edit_expense_form_prefilled_description(self, authenticated_client, test_user, test_expense):
        """Test that the description field is pre-filled with current value."""
        response = authenticated_client.get(f'/expenses/{test_expense["id"]}/edit')
        response_text = response.data.decode()
        assert 'Restaurant dinner' in response_text

    def test_edit_expense_form_category_preselected(self, authenticated_client, test_user, test_expense):
        """Test that the category dropdown has the correct category pre-selected."""
        response = authenticated_client.get(f'/expenses/{test_expense["id"]}/edit')
        response_text = response.data.decode()
        # Check for option with selected attribute for Food category
        assert 'value="Food" selected' in response_text or 'selected value="Food"' in response_text


class TestEditExpenseSuccessfulUpdate:
    """Test successful expense update functionality."""

    def test_edit_expense_valid_data_updates_database(self, authenticated_client, test_user, test_expense):
        """Test that POST with valid data updates the expense in database."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '250.00',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated description'
        })

        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

        # Verify the database was updated
        db = get_db()
        try:
            expense = db.execute(
                "SELECT * FROM expenses WHERE id = ?",
                (test_expense["id"],)
            ).fetchone()
            assert expense is not None
            assert expense['amount'] == 250.00
            assert expense['category'] == 'Shopping'
            assert expense['date'] == '2026-05-15'
            assert expense['description'] == 'Updated description'
            assert expense['user_id'] == test_user['id']  # Ownership preserved
        finally:
            db.close()

    def test_edit_expense_updated_values_visible_on_dashboard(self, authenticated_client, test_user, test_expense):
        """Test that updated values appear on dashboard after redirect."""
        # Update the expense
        authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '300.50',
            'category': 'Entertainment',
            'date': '2026-05-16',
            'description': 'Movie night'
        })

        # Check dashboard shows updated values
        response = authenticated_client.get('/dashboard')
        response_text = response.data.decode()
        assert '₹300.50' in response_text
        assert 'Entertainment' in response_text
        assert 'Movie night' in response_text


class TestEditExpenseValidation:
    """Test validation rules for edit expense form submission."""

    def test_edit_expense_zero_amount_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that amount = 0 shows error message and keeps submitted values."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '0',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated description'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()
        # Should keep submitted values
        assert 'Shopping' in response_text
        assert 'Updated description' in response_text

    def test_edit_expense_missing_amount_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that missing amount shows error message."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': 'Updated description'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()

    def test_edit_expense_invalid_date_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that invalid date shows error message."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '100.00',
            'category': 'Shopping',
            'date': 'invalid-date',
            'description': 'Updated description'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()

    def test_edit_expense_invalid_category_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that category not in fixed list shows error."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '100.00',
            'category': 'InvalidCategory',
            'date': '2026-05-15',
            'description': 'Updated description'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()

    def test_edit_expense_description_too_long_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that description longer than 200 chars is rejected."""
        long_description = 'a' * 201  # 201 characters
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '100.00',
            'category': 'Shopping',
            'date': '2026-05-15',
            'description': long_description
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()


class TestDashboardEditLinks:
    """Test edit links on the dashboard."""

    def test_dashboard_shows_edit_links(self, authenticated_client, test_user, test_expense):
        """Test that dashboard expense table shows Edit link for each expense."""
        response = authenticated_client.get('/dashboard')
        assert response.status_code == 200
        response_text = response.data.decode()

        # Should contain edit link pointing to the expense
        assert f'/expenses/{test_expense["id"]}/edit' in response_text
        assert 'Edit' in response_text


class TestAddExpenseFormStillWorks:
    """Test that Add Expense form still works after template changes."""

    def test_add_expense_form_page_title_correct(self, authenticated_client, test_user):
        """Test that Add Expense form page title says 'Add Expense'."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'Add Expense' in response_text

    def test_add_expense_form_submit_button_correct(self, authenticated_client, test_user):
        """Test that Add Expense form submit button says 'Add Expense'."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200
        response_text = response.data.decode()
        # Check for submit button with correct text
        assert 'Add Expense' in response_text

    def test_add_expense_form_still_functional(self, authenticated_client, test_user):
        """Test that Add Expense form can still create new expenses."""
        response = authenticated_client.post('/expenses/add', data={
            'amount': '99.99',
            'category': 'Food',
            'date': '2026-05-20',
            'description': 'Test expense'
        })

        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

        # Verify expense was created
        db = get_db()
        try:
            expense = db.execute(
                "SELECT * FROM expenses WHERE description = ? AND user_id = ?",
                ('Test expense', test_user['id'])
            ).fetchone()
            assert expense is not None
            assert expense['amount'] == 99.99
            assert expense['category'] == 'Food'
        finally:
            db.close()


class TestEditExpenseEdgeCases:
    """Test edge cases and boundary values."""

    def test_edit_expense_negative_amount_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that negative amount shows error."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '-50.00',
            'category': 'Food',
            'date': '2026-05-15',
            'description': 'Negative amount'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()

    def test_edit_expense_maximum_valid_amount(self, authenticated_client, test_user, test_expense):
        """Test that maximum valid amount (1,000,000) is accepted."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '1000000',
            'category': 'Other',
            'date': '2026-05-15',
            'description': 'Maximum amount'
        })

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

    def test_edit_expense_above_maximum_amount_shows_error(self, authenticated_client, test_user, test_expense):
        """Test that amount above 1,000,000 shows error."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '1000001',
            'category': 'Other',
            'date': '2026-05-15',
            'description': 'Above maximum'
        })

        assert response.status_code == 200
        response_text = response.data.decode()
        assert 'error' in response_text.lower() or 'invalid' in response_text.lower()

    def test_edit_expense_empty_description_allowed(self, authenticated_client, test_user, test_expense):
        """Test that empty description is allowed."""
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-05-15',
            'description': ''
        })

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

        # Verify in database
        db = get_db()
        try:
            expense = db.execute(
                "SELECT * FROM expenses WHERE id = ?",
                (test_expense["id"],)
            ).fetchone()
            assert expense['description'] == ''
        finally:
            db.close()

    def test_edit_expense_exactly_200_char_description_allowed(self, authenticated_client, test_user, test_expense):
        """Test that description of exactly 200 characters is allowed."""
        description_200 = 'a' * 200  # exactly 200 characters
        response = authenticated_client.post(f'/expenses/{test_expense["id"]}/edit', data={
            'amount': '50.00',
            'category': 'Food',
            'date': '2026-05-15',
            'description': description_200
        })

        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')
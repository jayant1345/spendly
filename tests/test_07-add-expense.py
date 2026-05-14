"""
Tests for the Add Expense feature (Spec 07).

Tests validate the /expenses/add route functionality, covering both GET and POST
operations with all validation rules from the spec's Definition of Done checklist.
"""
import pytest
from database.db import get_db
from datetime import datetime


class TestAddExpenseAuthentication:
    """Test authentication requirements for add expense functionality."""

    def test_add_expense_unauthenticated_redirects_to_login(self, client):
        """Test that visiting /expenses/add without login redirects to /login."""
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/login?next=/expenses/add')


class TestAddExpenseGetForm:
    """Test GET /expenses/add form rendering and content."""

    def test_add_expense_get_returns_200(self, authenticated_client, test_user):
        """Test that GET /expenses/add while logged in returns HTTP 200 with form."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200

    def test_add_expense_form_contains_required_fields(self, authenticated_client, test_user):
        """Test that form contains amount, category, date, description fields."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200

        content = response.data.decode()

        # Check for form fields
        assert 'name="amount"' in content
        assert 'name="category"' in content
        assert 'name="date"' in content
        assert 'name="description"' in content

        # Check for submit button
        assert 'Add Expense' in content

    def test_add_expense_date_field_prefilled_with_today(self, authenticated_client, test_user):
        """Test that date field is pre-filled with today's date."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200

        content = response.data.decode()
        today = datetime.now().strftime("%Y-%m-%d")

        # Check that today's date appears as the value in the date field
        assert f'value="{today}"' in content

    def test_add_expense_category_dropdown_contains_all_eight_categories(self, authenticated_client, test_user):
        """Test that category dropdown contains all 8 fixed categories."""
        response = authenticated_client.get('/expenses/add')
        assert response.status_code == 200

        content = response.data.decode()

        # Check all 8 fixed categories are present
        expected_categories = [
            "Bills", "Education", "Entertainment", "Food",
            "Health", "Other", "Shopping", "Transport"
        ]

        for category in expected_categories:
            assert category in content


class TestAddExpensePostSuccess:
    """Test successful POST /expenses/add operations."""

    def test_add_expense_post_valid_data_inserts_and_redirects(self, authenticated_client, test_user):
        """Test that submitting valid data inserts row and redirects to dashboard."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '123.45',
            'category': 'Food',
            'date': '2026-05-10',
            'description': 'Test expense'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should redirect to dashboard
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

        # Should have inserted exactly one new expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count + 1

        # Verify the expense was inserted with correct data
        expense = self._get_latest_expense(test_user['id'])
        assert expense['amount'] == 123.45
        assert expense['category'] == 'Food'
        assert expense['date'] == '2026-05-10'
        assert expense['description'] == 'Test expense'

    def test_add_expense_post_no_description_succeeds_stores_null(self, authenticated_client, test_user):
        """Test that submitting without description succeeds and stores NULL."""
        form_data = {
            'amount': '50.00',
            'category': 'Transport',
            'date': '2026-05-12',
            'description': ''  # Blank description
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should succeed and redirect
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/dashboard')

        # Verify description is NULL (None) in database
        expense = self._get_latest_expense(test_user['id'])
        assert expense['description'] is None

    def test_add_expense_appears_on_dashboard_after_redirect(self, authenticated_client, test_user):
        """Test that new expense appears on dashboard immediately after redirect."""
        form_data = {
            'amount': '99.99',
            'category': 'Shopping',
            'date': '2026-05-13',
            'description': 'New purchase'
        }

        # Submit the expense
        authenticated_client.post('/expenses/add', data=form_data)

        # Follow redirect to dashboard
        dashboard_response = authenticated_client.get('/dashboard')
        assert dashboard_response.status_code == 200

        content = dashboard_response.data.decode()

        # Verify expense appears on dashboard
        assert '₹99.99' in content
        assert 'Shopping' in content
        assert 'New purchase' in content

    def _count_user_expenses(self, user_id):
        """Helper: Count expenses for a user."""
        db = get_db()
        try:
            count = db.execute(
                "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
                (user_id,)
            ).fetchone()[0]
            return count
        finally:
            db.close()

    def _get_latest_expense(self, user_id):
        """Helper: Get the most recently added expense for a user."""
        db = get_db()
        try:
            expense = db.execute(
                "SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            ).fetchone()
            return expense
        finally:
            db.close()


class TestAddExpenseValidationFailures:
    """Test POST /expenses/add validation error cases."""

    def test_add_expense_missing_amount_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that missing amount shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '',  # Missing amount
            'category': 'Food',
            'date': '2026-05-10',
            'description': 'Test'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'required' in content.lower()

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_zero_amount_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that zero amount shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '0',  # Zero amount
            'category': 'Food',
            'date': '2026-05-10',
            'description': 'Test'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'positive' in content.lower()

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_negative_amount_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that negative amount shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '-50.00',  # Negative amount
            'category': 'Food',
            'date': '2026-05-10',
            'description': 'Test'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'positive' in content.lower()

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_invalid_date_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that invalid date shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '100.00',
            'category': 'Food',
            'date': 'not-a-date',  # Invalid date
            'description': 'Test'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'date' in content.lower()

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_invalid_category_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that category not in fixed list shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        form_data = {
            'amount': '100.00',
            'category': 'InvalidCategory',  # Not in fixed list
            'date': '2026-05-10',
            'description': 'Test'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'category' in content.lower()

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_description_over_200_chars_shows_error_no_insert(self, authenticated_client, test_user):
        """Test that description longer than 200 characters shows error and does not insert."""
        initial_count = self._count_user_expenses(test_user['id'])

        long_description = 'x' * 201  # 201 characters

        form_data = {
            'amount': '100.00',
            'category': 'Food',
            'date': '2026-05-10',
            'description': long_description
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error, not redirect
        assert response.status_code == 200
        content = response.data.decode()
        assert 'error' in content.lower() or 'long' in content.lower() or '200' in content

        # Should not insert expense
        final_count = self._count_user_expenses(test_user['id'])
        assert final_count == initial_count

    def test_add_expense_validation_error_preserves_form_values(self, authenticated_client, test_user):
        """Test that validation errors preserve submitted values so user doesn't lose input."""
        form_data = {
            'amount': '',  # Invalid to trigger error
            'category': 'Food',
            'date': '2026-05-10',
            'description': 'My test description'
        }

        response = authenticated_client.post('/expenses/add', data=form_data)

        # Should return 200 with error
        assert response.status_code == 200
        content = response.data.decode()

        # Should preserve the valid values that were submitted
        assert 'Food' in content
        assert '2026-05-10' in content
        assert 'My test description' in content

    def _count_user_expenses(self, user_id):
        """Helper: Count expenses for a user."""
        db = get_db()
        try:
            count = db.execute(
                "SELECT COUNT(*) FROM expenses WHERE user_id = ?",
                (user_id,)
            ).fetchone()[0]
            return count
        finally:
            db.close()
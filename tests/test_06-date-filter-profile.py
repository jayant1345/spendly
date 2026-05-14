"""
Tests for the date filter profile feature (Spec 06).

Tests validate the profile page functionality with month-based filtering,
covering all requirements from the spec's Definition of Done checklist.
"""
import pytest
from database.db import get_db


class TestProfilePageAccess:
    """Test basic profile page access and authentication."""

    def test_profile_unauthenticated_redirects_to_login(self, client):
        """Test that visiting /profile without login redirects to /login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert response.headers['Location'].endswith('/login?next=/profile')

    def test_profile_authenticated_returns_200(self, authenticated_client, test_user, test_expenses):
        """Test that visiting /profile while logged in returns HTTP 200."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200


class TestProfilePageContent:
    """Test profile page displays correct user data and content."""

    def test_profile_shows_real_user_data(self, authenticated_client, test_user, test_expenses):
        """Test that profile page shows user's real name and email from database."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200

        content = response.data.decode()
        assert test_user['name'] in content
        assert test_user['email'] in content

    def test_profile_shows_real_stats_from_database(self, authenticated_client, test_user, test_expenses):
        """Test that stats row shows real totals computed from expenses table."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200

        content = response.data.decode()

        # Should show total amount (sum of all test expenses: 875.75)
        assert "₹875.75" in content

        # Should show transaction count (6 total expenses)
        assert "6" in content

    def test_profile_shows_real_transactions_from_database(self, authenticated_client, test_user, test_expenses):
        """Test that Recent Transactions table shows real rows ordered by date descending."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200

        content = response.data.decode()

        # Should include transaction descriptions and amounts
        assert "Groceries" in content
        assert "Bus ticket" in content
        assert "Electricity" in content
        assert "Restaurant" in content
        assert "Clothes" in content
        assert "Doctor visit" in content

    def test_profile_shows_month_filter_input(self, authenticated_client, test_user, test_expenses):
        """Test that month filter input is visible on the page."""
        response = authenticated_client.get('/profile')
        assert response.status_code == 200

        content = response.data.decode()
        assert 'type="month"' in content
        assert 'name="month"' in content


class TestMonthFilteringFunctionality:
    """Test month filtering functionality and URL handling."""

    def test_valid_month_filter_updates_url(self, authenticated_client, test_user, test_expenses):
        """Test that submitting valid month filter reloads page with month in URL."""
        response = authenticated_client.get('/profile?month=2026-04')
        assert response.status_code == 200

        # Verify the month parameter is processed
        content = response.data.decode()
        # Should show "April 2026" or similar month label
        assert "April 2026" in content

    def test_month_filter_shows_only_filtered_transactions(self, authenticated_client, test_user, test_expenses):
        """Test that when month filter is active, only transactions from that month appear."""
        response = authenticated_client.get('/profile?month=2026-04')
        assert response.status_code == 200

        content = response.data.decode()

        # Should include April 2026 transactions
        assert "Groceries" in content  # 2026-04-15
        assert "Bus ticket" in content  # 2026-04-20
        assert "Electricity" in content  # 2026-04-25

        # Should NOT include non-April transactions
        assert "Restaurant" not in content  # 2026-03-10
        assert "Clothes" not in content     # 2026-03-15
        assert "Doctor visit" not in content  # 2026-02-05

    def test_month_filter_shows_filtered_stats_only(self, authenticated_client, test_user, test_expenses):
        """Test that when month filter is active, stats reflect filtered period only."""
        response = authenticated_client.get('/profile?month=2026-04')
        assert response.status_code == 200

        content = response.data.decode()

        # April 2026 total: 100.50 + 50.00 + 200.00 = 350.50
        assert "₹350.50" in content

        # April 2026 transaction count: 3
        assert "3" in content

        # Should NOT show all-time totals
        assert "₹875.75" not in content

    def test_clear_filter_shows_all_time_data(self, authenticated_client, test_user, test_expenses):
        """Test that Clear link removes filter and shows all-time data."""
        # First, apply a filter
        response = authenticated_client.get('/profile?month=2026-04')
        content = response.data.decode()
        assert "₹350.50" in content  # Filtered amount

        # Then, clear the filter
        response = authenticated_client.get('/profile')
        assert response.status_code == 200

        content = response.data.decode()
        # Should show all-time totals again
        assert "₹875.75" in content
        assert "6" in content

    def test_month_with_no_expenses_shows_zero_stats(self, authenticated_client, test_user, test_expenses):
        """Test that month with no expenses shows zero totals and empty transaction table."""
        response = authenticated_client.get('/profile?month=2026-01')  # January has no expenses
        assert response.status_code == 200

        content = response.data.decode()

        # Should show zero amounts
        assert "₹0.00" in content

        # Should show zero transaction count
        assert "0" in content

        # Should show empty state or no transactions message
        # (The exact message depends on template implementation)

    def test_invalid_month_falls_back_to_all_time(self, authenticated_client, test_user, test_expenses):
        """Test that invalid month parameter does not crash and falls back to all-time view."""
        response = authenticated_client.get('/profile?month=bad')
        assert response.status_code == 200

        content = response.data.decode()

        # Should show all-time totals (fallback behavior)
        assert "₹875.75" in content
        assert "6" in content

        # Should include all transactions
        assert "Groceries" in content
        assert "Restaurant" in content
        assert "Doctor visit" in content


class TestEdgeCasesAndValidation:
    """Test edge cases and input validation."""

    def test_malformed_month_parameter_fallback(self, authenticated_client, test_user, test_expenses):
        """Test various malformed month parameters fall back gracefully."""
        test_cases = [
            '/profile?month=',           # Empty string
            '/profile?month=2026',       # Year only
            '/profile?month=04',         # Month only
            '/profile?month=2026-13',    # Invalid month
            '/profile?month=2026-00',    # Invalid month
            '/profile?month=abc-def',    # Non-numeric
            '/profile?month=2026-4',     # Single digit month
        ]

        for url in test_cases:
            response = authenticated_client.get(url)
            assert response.status_code == 200

            content = response.data.decode()
            # Should show all-time data as fallback
            assert "₹875.75" in content

    def test_future_month_shows_empty_results(self, authenticated_client, test_user, test_expenses):
        """Test that filtering by a future month shows zero results."""
        response = authenticated_client.get('/profile?month=2027-12')  # Future month
        assert response.status_code == 200

        content = response.data.decode()

        # Should show zero stats
        assert "₹0.00" in content
        assert "0" in content

    def test_month_filter_with_no_user_expenses(self, authenticated_client):
        """Test month filtering for user with no expenses."""
        # Create a user with no expenses
        from database.db import get_db
        from werkzeug.security import generate_password_hash

        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Empty User", "empty@example.com", generate_password_hash("password123"))
            )
            user_id = cursor.lastrowid
            db.commit()
        finally:
            db.close()

        # Log in as this user
        with authenticated_client.session_transaction() as sess:
            sess['user_id'] = user_id
            sess['user_name'] = "Empty User"

        response = authenticated_client.get('/profile?month=2026-04')
        assert response.status_code == 200

        content = response.data.decode()

        # Should show zero stats
        assert "₹0.00" in content
        assert "0" in content

    def test_profile_preserves_month_in_form_input(self, authenticated_client, test_user, test_expenses):
        """Test that month filter form input is pre-filled with active month."""
        response = authenticated_client.get('/profile?month=2026-04')
        assert response.status_code == 200

        content = response.data.decode()

        # Month input should be pre-filled with the active month
        assert 'value="2026-04"' in content

    def test_multiple_users_data_isolation(self, client, test_user, test_expenses):
        """Test that users only see their own data when filtering."""
        # Create a second user with different expenses
        from database.db import get_db
        from werkzeug.security import generate_password_hash

        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Jane Doe", "jane@example.com", generate_password_hash("password123"))
            )
            user2_id = cursor.lastrowid

            # Add expenses for second user in April 2026
            db.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                (user2_id, 999.99, "Other", "2026-04-01", "Jane's expense")
            )
            db.commit()
        finally:
            db.close()

        # Log in as the first user
        with client.session_transaction() as sess:
            sess['user_id'] = test_user['id']
            sess['user_name'] = test_user['name']

        response = client.get('/profile?month=2026-04')
        assert response.status_code == 200

        content = response.data.decode()

        # Should see own expenses
        assert "Groceries" in content

        # Should NOT see other user's expenses
        assert "Jane's expense" not in content
        assert "₹999.99" not in content


class TestTopCategoryCalculation:
    """Test top category calculation with filtering."""

    def test_top_category_reflects_filtered_period(self, authenticated_client, test_user):
        """Test that top category calculation respects month filter."""
        # Create specific expenses to test top category logic
        from database.db import get_db

        db = get_db()
        try:
            # April 2026: Food (2 transactions), Transport (1 transaction)
            expenses = [
                (test_user['id'], 100.00, "Food", "2026-04-01", "Food 1"),
                (test_user['id'], 200.00, "Food", "2026-04-02", "Food 2"),  # Food should be top in April
                (test_user['id'], 50.00, "Transport", "2026-04-03", "Transport 1"),

                # March 2026: Transport (2 transactions), Food (1 transaction)
                (test_user['id'], 100.00, "Transport", "2026-03-01", "Transport 2"),
                (test_user['id'], 200.00, "Transport", "2026-03-02", "Transport 3"),  # Transport should be top in March
                (test_user['id'], 50.00, "Food", "2026-03-03", "Food 3"),
            ]

            db.executemany(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                expenses
            )
            db.commit()
        finally:
            db.close()

        # Test April filter - Food should be top category
        response = authenticated_client.get('/profile?month=2026-04')
        content = response.data.decode()
        assert "Food" in content  # Should appear as top category

        # Test March filter - Transport should be top category
        response = authenticated_client.get('/profile?month=2026-03')
        content = response.data.decode()
        assert "Transport" in content  # Should appear as top category
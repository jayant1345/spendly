import pytest
import tempfile
import os
from app import app
from database.db import init_db
from werkzeug.security import generate_password_hash


@pytest.fixture
def app_instance():
    """Create a Flask app configured for testing."""
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True

    # Override the DB_PATH in the database module to use our test database
    import database.db as db_module
    original_db_path = db_module.DB_PATH
    db_module.DB_PATH = db_path

    with app.app_context():
        init_db()

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)
    db_module.DB_PATH = original_db_path


@pytest.fixture
def client(app_instance):
    """Create a test client."""
    return app_instance.test_client()


@pytest.fixture
def authenticated_client(client, test_user):
    """Create a test client with a logged-in user."""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user['id']
        sess['user_name'] = test_user['name']
    return client


@pytest.fixture
def test_user():
    """Create a test user in the database."""
    from database.db import get_db

    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("John Doe", "john@example.com", generate_password_hash("password123"))
        )
        user_id = cursor.lastrowid
        db.commit()
        return {
            'id': user_id,
            'name': "John Doe",
            'email': "john@example.com"
        }
    finally:
        db.close()


@pytest.fixture
def test_expenses(test_user):
    """Create test expenses for the user."""
    from database.db import get_db

    db = get_db()
    try:
        # Expenses from different months for filtering tests
        expenses = [
            # April 2026 expenses
            (test_user['id'], 100.50, "Food", "2026-04-15", "Groceries"),
            (test_user['id'], 50.00, "Transport", "2026-04-20", "Bus ticket"),
            (test_user['id'], 200.00, "Bills", "2026-04-25", "Electricity"),

            # March 2026 expenses
            (test_user['id'], 75.25, "Food", "2026-03-10", "Restaurant"),
            (test_user['id'], 300.00, "Shopping", "2026-03-15", "Clothes"),

            # February 2026 expenses
            (test_user['id'], 150.00, "Health", "2026-02-05", "Doctor visit"),
        ]

        db.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
        db.commit()
        return expenses
    finally:
        db.close()
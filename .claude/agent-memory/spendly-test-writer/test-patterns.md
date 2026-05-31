---
name: test-patterns-spendly
description: Common test patterns, fixture conventions, and assertion approaches used in Spendly pytest tests
metadata:
  type: reference
---

## Fixture Patterns

### Standard Fixtures in conftest.py
- `app_instance` - Flask app with TESTING=True and temporary SQLite DB
- `client` - Unauthenticated test client  
- `authenticated_client` - Test client with logged-in user session
- `test_user` - Primary test user (John Doe, john@example.com)
- `test_expenses` - Sample expenses for the test user across multiple months

### Custom Fixtures in Test Files
- Feature-specific fixtures go in individual test files, not conftest.py
- Use `generate_password_hash` for password creation
- Always close DB connections in finally blocks
- Return dict structures with relevant fields for easy access

## Test Organization

### Class Structure
Group related tests by scenario:
- `TestFeatureAuthentication` - auth/login requirements
- `TestFeatureNotFound` - 404 error cases  
- `TestFeatureOwnership` - 403 ownership enforcement
- `TestFeatureGetForm` - GET request form rendering
- `TestFeatureSuccessfulUpdate` - happy path operations
- `TestFeatureValidation` - validation error cases
- `TestFeatureEdgeCases` - boundary values and edge cases

### Naming Convention
- `test_<feature>_<scenario>_<expected_outcome>`
- Use descriptive names that clearly map to spec requirements
- Example: `test_edit_expense_other_users_expense_returns_403`

## Assertion Patterns

### HTTP Status Codes
```python
assert response.status_code == 302
assert response.status_code == 200
assert response.status_code == 404
assert response.status_code == 403
```

### Redirects
```python
assert response.headers['Location'].endswith('/dashboard')
assert '/login' in response.headers['Location']
```

### Response Content
```python
response_text = response.data.decode()
assert 'Expected text' in response_text
assert 'error' in response_text.lower()
assert '₹150.50' in response_text  # Currency formatting
```

### Database State
```python
db = get_db()
try:
    record = db.execute("SELECT * FROM table WHERE id = ?", (id,)).fetchone()
    assert record['field'] == expected_value
finally:
    db.close()
```

## Authentication Testing
- Always test both authenticated and unauthenticated access
- Use session manipulation for login simulation:
```python
with client.session_transaction() as sess:
    sess['user_id'] = test_user['id']
    sess['user_name'] = test_user['name']
```

## Database Testing
- Use temporary DB per test via conftest.py app_instance fixture
- Query DB directly for side effect verification - this is acceptable
- Do NOT import business logic functions - use HTTP interface only
- Always use parameterized queries
- Test ownership with multiple users

## Validation Testing
- Test zero/negative amounts
- Test maximum allowed values (1,000,000 for amounts)
- Test invalid dates, categories not in CATEGORIES list
- Test description length limits (200 chars max)
- Test empty/missing required fields
- Assert error messages appear and submitted values are retained

## Form Testing
- Check pre-filled values with exact strings
- Test dropdown selections with `selected` attribute
- Verify form action URLs and button text
- Test that forms still work after template changes
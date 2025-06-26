import pytest
import os
import sqlite3
from student_app import app, init_db

TEST_DB = 'test_database.db'

# ✅ Fixture to setup and teardown test client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = TEST_DB
    app.secret_key = 'test_key'

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # ✅ Ensure correct database is initialized
    init_db(app.config['DATABASE'])

    with app.test_client() as client:
        yield client

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# ✅ Helper to check if table exists
def table_exists(conn, table_name):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None
def test_db_initialization():
    # Ensure test DB is created fresh
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # ✅ Initialize the database before checking
    init_db(TEST_DB)

    conn = sqlite3.connect(TEST_DB)
    try:
        assert table_exists(conn, 'users'), "'users' table missing"
        assert table_exists(conn, 'courses'), "'courses' table missing"
        assert table_exists(conn, 'enrollments'), "'enrollments' table missing"
    finally:
        conn.close()


# ✅ Signup + login
def test_user_signup_and_login(client):
    # Signup
    signup_response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass'
    })

    assert b'User created successfully' in signup_response.data or b'already exists' in signup_response.data

    # Login
    login_response = client.post('/', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'Dashboard' in login_response.data

# ✅ Role-based route restriction
def test_user_cannot_access_add_course(client):
    # Signup and login as regular user
    client.post('/signup', data={'username': 'user1', 'password': 'pass'})
    client.post('/', data={'username': 'user1', 'password': 'pass'}, follow_redirects=True)

    rv = client.get('/add_course', follow_redirects=True)

    # User should not see 'Add Course' form
    assert b'Add Course' not in rv.data

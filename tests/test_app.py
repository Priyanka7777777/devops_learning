import pytest
import os
import sqlite3
from student_app import app, init_db

TEST_DB = 'test_database.db'

# Helper to verify table existence
def table_exists(conn, table_name):
    try:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Error checking table {table_name}: {e}")
        return False

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = TEST_DB

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Initialize DB
    init_db(TEST_DB)

    with app.test_client() as client:
        yield client

    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_db_initialization():
    conn = sqlite3.connect(TEST_DB)
    try:
        assert table_exists(conn, 'users'), "'users' table missing"
        assert table_exists(conn, 'courses'), "'courses' table missing"
        assert table_exists(conn, 'enrollments'), "'enrollments' table missing"
    finally:
        conn.close()

def test_home_page_loads(client):
    rv = client.get('/')
    assert b'Login' in rv.data

def test_user_signup_and_login(client):
    # Signup
    try:
        signup_response = client.post('/signup', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        assert b'User created successfully' in signup_response.data or b'already exists' in signup_response.data
    except Exception as e:
        pytest.fail(f"Signup failed with error: {e}")

    # Login
    try:
        login_response = client.post('/', data={
            'username': 'testuser',
            'password': 'testpass'
        }, follow_redirects=True)
        assert b'Dashboard' in login_response.data
    except Exception as e:
        pytest.fail(f"Login failed with error: {e}")

def test_user_cannot_access_add_course(client):
    try:
        client.post('/signup', data={'username': 'user1', 'password': 'pass'})
        client.post('/', data={'username': 'user1', 'password': 'pass'}, follow_redirects=True)

        rv = client.get('/add_course', follow_redirects=True)
        assert b'Add Course' not in rv.data
    except Exception as e:
        pytest.fail(f"Access check for /add_course failed with error: {e}")

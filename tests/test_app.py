import pytest
import os
import sqlite3
from student_app import app, init_db

TEST_DB = 'test_database.db'

@pytest.fixture
def client():
    # Ensure a clean test database
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    app.config['TESTING'] = True
    app.config['DATABASE'] = TEST_DB

    # Initialize test DB with required tables
    init_db(TEST_DB)

    with app.test_client() as client:
        yield client

    # Optionally clean up the test DB after test session
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_home_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_user_signup_and_login(client):
    # Sign up a test user
    response = client.post('/signup', data={'username': 'testuser', 'password': 'testpass'})
    assert b'User created successfully' in response.data

    # Login with the new user
    response = client.post('/', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_admin_dashboard_requires_login(client):
    # Try accessing dashboard without login
    response = client.get('/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data


def test_user_cannot_access_add_course(client):
    # Register and login as a normal user
    client.post('/signup', data={'username': 'user1', 'password': 'pass'})
    client.post('/', data={'username': 'user1', 'password': 'pass'}, follow_redirects=True)

    # Try to access the add_course page
    response = client.get('/add_course', follow_redirects=True)
    assert response.status_code == 200
    assert b'Add Course' not in response.data  # Normal users should not see the form

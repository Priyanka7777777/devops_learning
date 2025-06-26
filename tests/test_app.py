import os
import sqlite3
import pytest

from student_app import app, init_db

TEST_DB = 'test_database.db'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = TEST_DB

    # Remove any existing test DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Initialize fresh test DB
    init_db(TEST_DB)

    with app.test_client() as client:
        yield client

    # Clean up test DB after test run
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_home_page_loads(client):
    response = client.get('/')
    assert b'Login' in response.data


def test_user_signup_and_login(client):
    # Signup step
    signup_response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'login' in signup_response.data.lower() or signup_response.status_code == 200

    # Login step
    login_response = client.post('/', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'Dashboard' in login_response.data


def test_admin_dashboard_requires_login(client):
    response = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in response.data


def test_user_cannot_access_add_course(client):
    # Register and login as a normal user
    client.post('/signup', data={'username': 'user1', 'password': 'pass'})
    client.post('/', data={'username': 'user1', 'password': 'pass'}, follow_redirects=True)

    response = client.get('/add_course', follow_redirects=True)

    # Should be redirected to dashboard, not allowed to access add_course
    assert b'Add Course' not in response.data
    assert b'Dashboard' in response.data

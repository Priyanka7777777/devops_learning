import pytest
import os
import sqlite3

from student_app import app, init_db

TEST_DB = 'test_database.db'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = TEST_DB

    # Clean up any existing test DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # ✅ Ensure test DB gets initialized
    init_db(TEST_DB)

    with app.test_client() as client:
        yield client

    # Cleanup after tests
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_home_page_loads(client):
    rv = client.get('/')
    assert b'Login' in rv.data

def test_user_signup_and_login(client):
    # Signup
    signup_response = client.post('/signup', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert b'User created successfully' in signup_response.data

    # Login
    login_response = client.post('/', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)

    assert b'Dashboard' in login_response.data

def test_admin_dashboard_requires_login(client):
    rv = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in rv.data

def test_user_cannot_access_add_course(client):
    client.post('/signup', data={'username': 'user1', 'password': 'pass'})
    client.post('/', data={'username': 'user1', 'password': 'pass'}, follow_redirects=True)

    rv = client.get('/add_course', follow_redirects=True)
    assert b'Add Course' not in rv.data  # User shouldn't see Add Course

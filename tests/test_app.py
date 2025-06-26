import pytest
import tempfile
import os

from student_app import app, init_db, get_db_connection

@pytest.fixture
def client():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['DATABASE'] = db_path

    # Initialize the temporary DB
    init_db(db_path)

    # Create test client
    with app.test_client() as client:
        yield client

    # Clean up after test
    os.close(db_fd)
    os.unlink(db_path)

def test_home_page_loads(client):
    rv = client.get('/')
    assert b'Login' in rv.data

def test_user_signup_and_login(client):
    # Signup
    rv = client.post('/signup', data={'username': 'testuser', 'password': 'testpass'})
    assert b'User created successfully' in rv.data

    # Login
    rv = client.post('/', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Dashboard' in rv.data

def test_admin_dashboard_requires_login(client):
    rv = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in rv.data

def test_user_cannot_access_add_course(client):
    # Signup + login
    client.post('/signup', data={'username': 'user1', 'password': 'pass'})
    client.post('/', data={'username': 'user1', 'password': 'pass'})

    # Try accessing add_course
    rv = client.get('/add_course', follow_redirects=True)
    assert b'Add Course' not in rv.data

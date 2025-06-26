import pytest

from student_app import app, init_db, get_db_connection


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_database.db'
    init_db()
    with app.test_client() as client:
        yield client

def test_home_page_loads(client):
    rv = client.get('/')
    assert b'Login' in rv.data

def test_user_signup_and_login(client):
    # Signup
    rv = client.post('/signup', data={'username': 'testuser', 'password': 'testpass'})
    assert b'User created successfully' in rv.data

    # Login
    rv = client.post('/', data={'username': 'testuser', 'password': 'testpass'}, follow_redirects=True)
    assert b'Dashboard' in rv.data or rv.status_code == 200

def test_admin_dashboard_requires_login(client):
    rv = client.get('/dashboard', follow_redirects=True)
    assert b'Login' in rv.data

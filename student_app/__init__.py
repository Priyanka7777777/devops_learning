from flask import Flask, render_template, request, redirect, session, url_for
import os
from dotenv import load_dotenv
import sqlite3

# Load environment from .env or fallback
env_file = os.getenv('ENV_FILE', '.env')
load_dotenv(dotenv_path=env_file)

# Create Flask app
app = Flask(__name__, template_folder='templates')  # Ensure templates path
env = os.getenv('FLASK_ENV', 'development')

# Load configuration
import config
if env == 'development':
    app.config.from_object(config.DevelopmentConfig)
elif env == 'production':
    app.config.from_object(config.ProductionConfig)
elif env == 'testing':
    app.config.from_object(config.TestingConfig)
else:
    app.config.from_object(config.Config)

app.secret_key = app.config['SECRET_KEY']
DATABASE = app.config['DATABASE']

# Initialize database
def init_db(database_path=None):
    db_path = database_path or DATABASE
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_name TEXT NOT NULL,
                        description TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS enrollments (
                        user_id INTEGER,
                        course_id INTEGER,
                        PRIMARY KEY (user_id, course_id),
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(course_id) REFERENCES courses(id))''')
        conn.commit()

# Get DB connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                                (username, password)).fetchone()
        if user:
            session['user'] = {'id': user['id'], 'username': user['username'], 'role': user['role']}
            return redirect('/dashboard')
        return 'Invalid Credentials'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        user = session['user']
        with get_db_connection() as conn:
            courses = conn.execute('SELECT * FROM courses').fetchall()
            if user['role'] == 'admin':
                students = conn.execute("SELECT * FROM users WHERE role='user'").fetchall()
                enrollments = conn.execute('''
                    SELECT e.user_id, e.course_id, u.username, c.course_name 
                    FROM enrollments e
                    JOIN users u ON e.user_id = u.id
                    JOIN courses c ON e.course_id = c.id
                ''').fetchall()
                return render_template('dashboard.html', user=user, courses=courses, students=students, enrollments=enrollments)
        return render_template('dashboard.html', user=user, courses=courses)
    return redirect('/')

@app.route('/remove_enrollment/<int:user_id>/<int:course_id>')
def remove_enrollment(user_id, course_id):
    if 'user' in session and session['user']['role'] == 'admin':
        with get_db_connection() as conn:
            conn.execute('DELETE FROM enrollments WHERE user_id = ? AND course_id = ?', (user_id, course_id))
            conn.commit()
    return redirect('/dashboard')

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user' in session and session['user']['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            desc = request.form['desc']
            with get_db_connection() as conn:
                conn.execute('INSERT INTO courses (course_name, description) VALUES (?, ?)', (name, desc))
                conn.commit()
            return redirect('/dashboard')
        return render_template('add_course.html')
    return redirect('/dashboard')

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'user' in session and session['user']['role'] == 'user':
        user_id = session['user']['id']
        with get_db_connection() as conn:
            conn.execute('INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?, ?)', (user_id, course_id))
            conn.commit()
        return redirect('/dashboard')
    return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        msg = ''
        try:
            with get_db_connection() as conn:
                conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                             (username, password, 'user'))
                conn.commit()
                msg = 'User created successfully. Please login.'
        except sqlite3.IntegrityError:
            msg = 'Username already exists!'
        return render_template('signup.html', message=msg)
    return render_template('signup.html')

if __name__ == '__main__':
    init_db()
    app.run()

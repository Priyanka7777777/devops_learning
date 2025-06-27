from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
import sqlite3
from dotenv import load_dotenv

# Load environment variables
env_file = os.getenv('ENV_FILE', '.env')
load_dotenv(dotenv_path=env_file)

app = Flask(__name__, template_folder='templates')
env = os.getenv('FLASK_ENV', 'development')

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

def init_db(database_path=None):
    db_path = database_path or app.config['DATABASE']
    try:
        conn = sqlite3.connect(db_path)
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
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to initialize DB: {e}")
        raise

def get_db_connection():
    try:
        db_path = app.config['DATABASE']
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"[ERROR] Could not connect to DB: {e}")
        raise

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?',
                (username, password)).fetchone()
        if user:
            session['user'] = {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
            return redirect('/dashboard')
        return render_template('login.html', message='Invalid Credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    user = session['user']
    with get_db_connection() as conn:
        courses = conn.execute('SELECT * FROM courses').fetchall()
        enrollments = conn.execute(
            'SELECT course_id FROM enrollments WHERE user_id = ?',
            (user['id'],)).fetchall()
        enrolled_course_ids = {row['course_id'] for row in enrollments}

        if user['role'] == 'admin':
            students = conn.execute("SELECT * FROM users WHERE role='user'").fetchall()
            all_enrollments = conn.execute('''
                SELECT e.user_id, e.course_id, u.username, c.course_name 
                FROM enrollments e
                JOIN users u ON e.user_id = u.id
                JOIN courses c ON e.course_id = c.id
            ''').fetchall()
            return render_template('dashboard.html', user=user, courses=courses,
                                   students=students, enrollments=all_enrollments)

    return render_template('dashboard.html', user=user, courses=courses, enrolled_ids=enrolled_course_ids)

@app.route('/remove_enrollment/<int:user_id>/<int:course_id>')
def remove_enrollment(user_id, course_id):
    if 'user' in session and session['user']['role'] == 'admin':
        with get_db_connection() as conn:
            conn.execute('DELETE FROM enrollments WHERE user_id = ? AND course_id = ?',
                         (user_id, course_id))
            conn.commit()
    return redirect('/dashboard')

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user' not in session or session['user']['role'] != 'admin':
        return redirect('/dashboard')

    if request.method == 'POST':
        name = request.form['name']
        desc = request.form['desc']
        with get_db_connection() as conn:
            conn.execute('INSERT INTO courses (course_name, description) VALUES (?, ?)',
                         (name, desc))
            conn.commit()
        return redirect('/dashboard')

    return render_template('add_course.html')

@app.route('/enroll/<int:course_id>', methods=['GET'])
def enroll(course_id):
    if 'user' not in session or session['user']['role'] != 'user':
        return redirect('/')

    user_id = session['user']['id']
    with get_db_connection() as conn:
        existing = conn.execute(
            'SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?',
            (user_id, course_id)).fetchone()

        if not existing:
            conn.execute(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                (user_id, course_id))
            conn.commit()
            flash('Successfully enrolled in the course.')

    return redirect('/dashboard')

@app.route('/unenroll/<int:course_id>', methods=['GET'])
def unenroll(course_id):
    if 'user' not in session or session['user']['role'] != 'user':
        return redirect('/')

    user_id = session['user']['id']
    with get_db_connection() as conn:
        conn.execute(
            'DELETE FROM enrollments WHERE user_id = ? AND course_id = ?',
            (user_id, course_id))
        conn.commit()
        flash('You have been unenrolled from the course.')

    return redirect('/dashboard')
@app.route('/remove_course/<int:course_id>', methods=['GET'])
def remove_course(course_id):
    if 'user' in session and session['user']['role'] == 'admin':
        with get_db_connection() as conn:
            conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
            conn.execute('DELETE FROM enrollments WHERE course_id = ?', (course_id,))
            conn.commit()
            flash('Course removed successfully.')
    return redirect('/dashboard')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        try:
            with get_db_connection() as conn:
                conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                             (username, password, 'user'))
                conn.commit()
                msg = 'User created successfully'
        except sqlite3.IntegrityError:
            msg = 'Username already exists!'
        except sqlite3.Error as e:
            msg = f'Database error: {e}'
    return render_template('signup.html', message=msg)

if __name__ == '__main__':
    db_path = app.config.get('DATABASE')
    if not db_path:
        raise RuntimeError("DATABASE config is not set.")
    if not os.path.exists(db_path):
        print(f"[INFO] Initializing DB at: {db_path}")
        init_db(db_path)
    app.run(debug=True)

# Simple 3-Tier Student Course Management System (Flask + SQLite)

from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from dotenv import load_dotenv
import config

# Load main .env file
load_dotenv()

# Load environment-specific .env file
env_file = os.getenv('ENV_FILE', '.env.development')
load_dotenv(dotenv_path=env_file)

app = Flask(__name__)

# Select environment
env = os.getenv('FLASK_ENV', 'development')

if env == 'development':
    app.config.from_object(config.DevelopmentConfig)
elif env == 'production':
    app.config.from_object(config.ProductionConfig)
elif env == 'testing':
    app.config.from_object(config.TestingConfig)
else:
    app.config.from_object(config.Config)

DATABASE = os.getenv('DATABASE')
app.secret_key = os.getenv('SECRET_KEY')

# Data Layer: Initialize DB if not exists
def init_db():
    if not os.path.exists(DATABASE):
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        role TEXT NOT NULL)''')
        c.execute('''CREATE TABLE courses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        course_name TEXT NOT NULL,
                        description TEXT)''')
        c.execute('''CREATE TABLE enrollments (
                        user_id INTEGER,
                        course_id INTEGER,
                        PRIMARY KEY (user_id, course_id),
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        FOREIGN KEY(course_id) REFERENCES courses(id))''')
        conn.commit()
        conn.close()

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
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        if user:
            session['user'] = {'id': user['id'], 'username': user['username'], 'role': user['role']}
            return redirect('/dashboard')
        else:
            return 'Invalid Credentials'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        user = session['user']
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses').fetchall()

        if user['role'] == 'admin':
            students = conn.execute("SELECT * FROM users WHERE role='user'").fetchall()
            enrollments = conn.execute('''SELECT e.user_id, e.course_id, u.username, c.course_name 
                                          FROM enrollments e
                                          JOIN users u ON e.user_id = u.id
                                          JOIN courses c ON e.course_id = c.id''').fetchall()
            conn.close()
            return render_template('dashboard.html', user=user, courses=courses, students=students, enrollments=enrollments)

        conn.close()
        return render_template('dashboard.html', user=user, courses=courses)
    return redirect('/')

@app.route('/remove_enrollment/<int:user_id>/<int:course_id>')
def remove_enrollment(user_id, course_id):
    if 'user' in session and session['user']['role'] == 'admin':
        conn = get_db_connection()
        conn.execute('DELETE FROM enrollments WHERE user_id = ? AND course_id = ?', (user_id, course_id))
        conn.commit()
        conn.close()
    return redirect('/dashboard')

@app.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user' in session and session['user']['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            desc = request.form['desc']
            conn = get_db_connection()
            conn.execute('INSERT INTO courses (course_name, description) VALUES (?, ?)',
                         (name, desc))
            conn.commit()
            conn.close()
            return redirect('/dashboard')
        return render_template('add_course.html')
    return redirect('/dashboard')

@app.route('/enroll/<int:course_id>')
def enroll(course_id):
    if 'user' in session and session['user']['role'] == 'user':
        user_id = session['user']['id']
        conn = get_db_connection()
        conn.execute('INSERT OR IGNORE INTO enrollments (user_id, course_id) VALUES (?, ?)',
                     (user_id, course_id))
        conn.commit()
        conn.close()
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
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (username, password, 'user'))
            conn.commit()
            msg = 'User created successfully. Please login.'
        except sqlite3.IntegrityError:
            msg = 'Username already exists!'
        conn.close()
        return msg
    return render_template('signup.html')

if __name__ == '__main__':
    init_db()
    app.run()

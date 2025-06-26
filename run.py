from student_app import app, init_db

if __name__ == '__main__':
    init_db()  # Optional: ensure DB initialized
    app.run()


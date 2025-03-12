import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # New config variable for the courses CSV file
    # If an environment variable COURSES_CSV_PATH is set, use that;
    # otherwise, default to 'courses.csv' in the same directory as this file.
    COURSES_CSV_PATH = os.environ.get('COURSES_CSV_PATH', os.path.join(basedir, 'courses.csv'))
    
    # Debug print to confirm the final path
    print("COURSES_CSV_PATH set to:", COURSES_CSV_PATH)

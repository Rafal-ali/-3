# Flask and DB config
SECRET_KEY = 'your-secret-key'
# Use a database path relative to the app directory
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'app', 'database', 'database.db')}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
LOGIN_DISABLED = False

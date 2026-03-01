# Initialize Flask app and load config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import logging

db = SQLAlchemy()
login_manager = LoginManager()

app = Flask(__name__)
app.config.from_pyfile('../config.py')

db.init_app(app)
login_manager.init_app(app)

# Logging setup
logging.basicConfig(filename='app/logs/app.log', level=logging.INFO)

from app.controllers import *
from app.controllers.auth_controller import bp as auth_bp
from app.controllers.parking_controller import bp as parking_bp
from app.controllers.analytics_controller import bp as analytics_bp
from app.controllers.iot_controller import bp as iot_bp
from app.controllers.log_controller import bp as log_bp
from app.views.dashboard import dashboard_bp
from app.views.parking import parking_management_bp
from app.views.log import log_view_bp
from app.views.users import user_management_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(parking_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(iot_bp)
app.register_blueprint(log_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(parking_management_bp)
app.register_blueprint(log_view_bp)
app.register_blueprint(user_management_bp)

# Main route redirects to login
@app.route('/')
def index():
    from flask import redirect, url_for
    return redirect(url_for('auth.login'))

# Create database tables
with app.app_context():
    db.create_all()
    # إنشاء مستخدم أولي إذا لم يوجد
    from app.models.user import User
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', password='admin123', role='admin')
        db.session.add(user)
    if not User.query.filter_by(username='operator').first():
        user = User(username='operator', password='operator123', role='operator')
        db.session.add(user)
        db.session.commit()

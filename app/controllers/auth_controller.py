# Authentication and role management
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.models.user import User
from app import db, login_manager
# --- Firebase imports ---
import pyrebase
from firebase_config import FIREBASE_CONFIG
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db_fb = firebase.database()

bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    from flask import render_template
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'operator')
        # --- تحقق من المستخدم في Firebase ---
        users_fb = db_fb.child("users").get().val() or {}
        user_fb = users_fb.get(username)
        import bcrypt
        if user_fb:
            if bcrypt.checkpw(password.encode('utf-8'), user_fb['password'].encode('utf-8')) and user_fb['role'] == role:
                # إنشاء مستخدم Flask-Login وهمي
                user_obj = type('User', (), {"id": username, "username": username, "role": user_fb['role'], "is_authenticated": True, "is_active": True, "is_anonymous": False, "get_id": lambda self: self.id})()
                login_user(user_obj)
                flash('تم تسجيل الدخول بنجاح (Firebase)', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('اسم المستخدم أو كلمة المرور أو الدور غير صحيح (Firebase)', 'danger')
        else:
            flash('اسم المستخدم غير موجود في Firebase، يرجى إنشاء حساب جديد.', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    from flask import render_template
    username = request.form['username']
    password = request.form['password']
    role = request.form.get('role', 'operator')
    # تحقق من وجود المستخدم في Firebase
    users_fb = db_fb.child("users").get().val() or {}
    if username in users_fb:
        flash('اسم المستخدم موجود بالفعل (Firebase)', 'danger')
        return redirect(url_for('auth.login'))
    import bcrypt
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    db_fb.child("users").child(username).set({"password": hashed_pw, "role": role})
    flash('تم إنشاء الحساب بنجاح (Firebase)، يمكنك تسجيل الدخول الآن.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))

# Authentication and role management
from flask import Blueprint, request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
from app import db, login_manager

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
        user = User.query.filter_by(username=username).first()
        if user:
            if user.check_password(password) and user.role == role:
                login_user(user)
                flash('Logged in successfully.', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Invalid username, password, or role.', 'danger')
        else:
            flash('اسم المستخدم غير موجود، يرجى إنشاء حساب جديد.', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    from flask import render_template
    username = request.form['username']
    password = request.form['password']
    role = request.form.get('role', 'operator')
    if User.query.filter_by(username=username).first():
        flash('اسم المستخدم موجود بالفعل', 'danger')
        return redirect(url_for('auth.login'))
    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('تم إنشاء الحساب بنجاح، يمكنك تسجيل الدخول الآن.', 'success')
    return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))

# User management view

from flask import render_template, Blueprint, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User
from app import db
# --- Firebase imports ---
import pyrebase
from firebase_config import FIREBASE_CONFIG
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db_fb = firebase.database()

user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    if current_user.role != 'admin':
        abort(403)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        # --- تحقق من وجود المستخدم في Firebase ---
        users_fb = db_fb.child("users").get().val() or {}
        if username in users_fb:
            flash('اسم المستخدم موجود بالفعل (Firebase)', 'danger')
        else:
            import bcrypt
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            db_fb.child("users").child(username).set({"password": hashed_pw, "role": role})
            flash('تم إضافة المستخدم بنجاح (Firebase)', 'success')
    # --- جلب المستخدمين من Firebase ---
    users_fb = db_fb.child("users").get().val() or {}
    users_list = []
    for uname, udata in users_fb.items():
        users_list.append(type('User', (), {"id": uname, "username": uname, "role": udata.get("role", "operator")})())
    return render_template('users.html', users=users_list)

@user_management_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    # حذف مستخدم من Firebase (اسم المستخدم هو المفتاح)
    username = str(user_id)  # في الكود الأصلي user_id هو رقم، في Firebase المفتاح هو الاسم
    if username == 'admin':
        flash('لا يمكن حذف هذا المستخدم', 'danger')
    else:
        db_fb.child("users").child(username).remove()
        flash('تم حذف المستخدم بنجاح (Firebase)', 'success')
    return redirect(url_for('user_management.users'))

@user_management_bp.route('/users/edit/<int:user_id>', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get(user_id)
    if user:
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        user.username = username
        user.password = password
        user.role = role
        db.session.commit()
        flash('تم تعديل المستخدم بنجاح', 'success')
    else:
        flash('المستخدم غير موجود', 'danger')
    return redirect(url_for('user_management.users'))

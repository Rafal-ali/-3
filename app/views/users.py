# User management view
from flask import render_template, Blueprint, abort, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import User
from app import db

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
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
        else:
            user = User(username=username, password=password, role=role)
            db.session.add(user)
            db.session.commit()
            flash('تم إضافة المستخدم بنجاح', 'success')
    users = User.query.all()
    return render_template('users.html', users=users)

@user_management_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        abort(403)
    user = User.query.get(user_id)
    if user and user.username != 'admin':
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح', 'success')
    else:
        flash('لا يمكن حذف هذا المستخدم', 'danger')
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

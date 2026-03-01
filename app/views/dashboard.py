# Dashboard view for admin/operator
from flask import render_template, Blueprint, abort
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'operator']:
        abort(403)
    # إضافة روابط لإدارة المواقف والتحليلات
    return render_template('dashboard.html', show_links=True)

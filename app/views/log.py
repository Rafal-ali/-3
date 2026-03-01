# Log view for operation log
from flask import render_template, Blueprint, abort
from flask_login import login_required, current_user

log_view_bp = Blueprint('log_view', __name__)

@log_view_bp.route('/logs')
@login_required
def logs():
    if current_user.role not in ['admin', 'operator']:
        abort(403)
    return render_template('log.html')

# Parking management view
from flask import render_template, Blueprint, abort
from flask_login import login_required, current_user

parking_management_bp = Blueprint('parking_management', __name__)

@parking_management_bp.route('/parking')
@login_required
def parking_page():
    if current_user.role not in ['admin', 'operator']:
        abort(403)
    return render_template('parking.html')

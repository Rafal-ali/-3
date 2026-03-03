# Analytics and revenue endpoints
from flask import Blueprint, jsonify

from app.models.parking import Vehicle
from app import db
# --- Firebase imports ---
import pyrebase
from firebase_config import FIREBASE_CONFIG
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db_fb = firebase.database()

bp = Blueprint('analytics', __name__)

@bp.route('/api/analytics', methods=['GET'])
def analytics():
    # Example: return number of vehicles per day from Firebase
    vehicles_fb = db_fb.child("vehicles").get().val() or {}
    from collections import Counter
    import datetime
    day_counts = Counter()
    for v_id, v in vehicles_fb.items():
        entry_time = v.get('entry_time')
        if entry_time:
            # يفترض أن entry_time هو نص تاريخ أو "now"
            day = entry_time.split('T')[0] if 'T' in entry_time else entry_time
            day_counts[day] += 1
    data = {'labels': list(day_counts.keys()), 'values': list(day_counts.values())}
    return jsonify(data)

@bp.route('/api/revenue', methods=['GET'])
def revenue():
    # Example: return revenue per day from Firebase (assume fixed price per vehicle)
    price_per_vehicle = 10
    vehicles_fb = db_fb.child("vehicles").get().val() or {}
    from collections import Counter
    day_counts = Counter()
    for v_id, v in vehicles_fb.items():
        exit_time = v.get('exit_time')
        if exit_time:
            day = exit_time.split('T')[0] if 'T' in exit_time else exit_time
            day_counts[day] += 1
    data = {'labels': list(day_counts.keys()), 'values': [c*price_per_vehicle for c in day_counts.values()]}
    return jsonify(data)

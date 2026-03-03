# Logging endpoints
from flask import Blueprint, jsonify

from app.models.log import Log
from app import db
# --- Firebase imports ---
import pyrebase
from firebase_config import FIREBASE_CONFIG
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db_fb = firebase.database()

bp = Blueprint('log', __name__)

@bp.route('/api/logs', methods=['GET'])
def get_logs():
    # جلب السجلات من Firebase
    logs_fb = db_fb.child("logs").get().val() or {}
    logs_data = []
    for log_id, log in logs_fb.items():
        logs_data.append({
            'timestamp': log.get('timestamp'),
            'action': log.get('action'),
            'user_id': log.get('user_id'),
            'details': log.get('details')
        })
    # ترتيب تنازلي حسب الوقت (إذا متوفر)
    logs_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify(logs_data[:100])

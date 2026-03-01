# Logging endpoints
from flask import Blueprint, jsonify
from app.models.log import Log
from app import db

bp = Blueprint('log', __name__)

@bp.route('/api/logs', methods=['GET'])
def get_logs():
    logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
    logs_data = [
        {'timestamp': log.timestamp, 'action': log.action, 'user_id': log.user_id, 'details': log.details}
        for log in logs
    ]
    return jsonify(logs_data)

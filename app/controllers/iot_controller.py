# IoT simulation endpoints
from flask import Blueprint, request, jsonify
from app.models.parking import ParkingSlot
from app import db

bp = Blueprint('iot', __name__)

@bp.route('/api/iot/update', methods=['POST'])
def iot_update():
    data = request.get_json()
    slot_id = data.get('slot_id')
    sensor_value = data.get('sensor_value')
    slot = ParkingSlot.query.get(slot_id)
    if slot:
        slot.sensor_value = sensor_value
        slot.status = 'occupied' if sensor_value else 'free'
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Slot not found'})

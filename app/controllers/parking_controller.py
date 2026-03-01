# Parking slot and vehicle management
from flask import Blueprint, request, jsonify
from app.models.parking import ParkingSlot, Vehicle
from app import db

bp = Blueprint('parking', __name__)

@bp.route('/api/slots', methods=['GET'])
def get_slots():
    slots = ParkingSlot.query.all()
    slots_data = [
        {'id': slot.id, 'status': slot.status, 'sensor_value': slot.sensor_value}
        for slot in slots
    ]
    return jsonify(slots_data)

@bp.route('/api/vehicle/entry', methods=['POST'])
def vehicle_entry():
    data = request.get_json()
    plate_number = data.get('plate_number')
    slot_id = data.get('slot_id')
    slot = ParkingSlot.query.get(slot_id)
    if slot and slot.status == 'free':
        slot.status = 'occupied'
        slot.sensor_value = True
        vehicle = Vehicle(plate_number=plate_number, entry_time=db.func.now(), slot_id=slot_id)
        db.session.add(vehicle)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Slot not available'})

@bp.route('/api/vehicle/exit', methods=['POST'])
def vehicle_exit():
    data = request.get_json()
    slot_id = data.get('slot_id')
    slot = ParkingSlot.query.get(slot_id)
    if slot and slot.status == 'occupied':
        slot.status = 'free'
        slot.sensor_value = False
        vehicle = Vehicle.query.filter_by(slot_id=slot_id, exit_time=None).first()
        if vehicle:
            vehicle.exit_time = db.func.now()
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Slot not occupied'})

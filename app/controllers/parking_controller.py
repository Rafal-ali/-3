# Parking slot and vehicle management
from flask import Blueprint, request, jsonify

from app.models.parking import ParkingSlot, Vehicle
from app import db
# --- Firebase imports ---
import pyrebase
from firebase_config import FIREBASE_CONFIG
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db_fb = firebase.database()

bp = Blueprint('parking', __name__)

@bp.route('/api/slots', methods=['GET'])
def get_slots():
    # جلب المواقف من Firebase
    slots_fb = db_fb.child("slots").get().val() or {}
    slots_data = []
    for slot_id, slot in slots_fb.items():
        slots_data.append({'id': slot_id, 'status': slot.get('status', 'free'), 'sensor_value': slot.get('sensor_value', False)})
    return jsonify(slots_data)

@bp.route('/api/vehicle/entry', methods=['POST'])
def vehicle_entry():
    data = request.get_json()
    plate_number = data.get('plate_number')
    slot_id = str(data.get('slot_id'))
    slot = db_fb.child("slots").child(slot_id).get().val()
    if slot and slot.get('status') == 'free':
        db_fb.child("slots").child(slot_id).update({"status": "occupied", "sensor_value": True, "car_number": plate_number})
        # إضافة سجل دخول مركبة (يمكنك توسيعها لاحقًا)
        db_fb.child("vehicles").push({"plate_number": plate_number, "entry_time": "now", "slot_id": slot_id})
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Slot not available'})

@bp.route('/api/vehicle/exit', methods=['POST'])
def vehicle_exit():
    data = request.get_json()
    slot_id = str(data.get('slot_id'))
    slot = db_fb.child("slots").child(slot_id).get().val()
    if slot and slot.get('status') == 'occupied':
        db_fb.child("slots").child(slot_id).update({"status": "free", "sensor_value": False, "car_number": None})
        # تحديث سجل المركبة (يمكنك توسيعها لاحقًا)
        # ملاحظة: هنا فقط يتم تحرير الموقف، ويمكنك إضافة منطق تحديث وقت الخروج في جدول المركبات
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Slot not occupied'})

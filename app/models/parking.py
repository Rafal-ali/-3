# Parking slot and vehicle models
from app import db

class ParkingSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), nullable=False)  # 'free', 'occupied'
    sensor_value = db.Column(db.Boolean, default=False)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(20), nullable=False)
    entry_time = db.Column(db.DateTime)
    exit_time = db.Column(db.DateTime)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slot.id'))

# Analytics and revenue endpoints
from flask import Blueprint, jsonify
from app.models.parking import Vehicle
from app import db

bp = Blueprint('analytics', __name__)

@bp.route('/api/analytics', methods=['GET'])
def analytics():
    # Example: return number of vehicles per day
    from sqlalchemy import func
    result = db.session.query(func.date(Vehicle.entry_time), func.count(Vehicle.id)).group_by(func.date(Vehicle.entry_time)).all()
    data = {'labels': [str(r[0]) for r in result], 'values': [r[1] for r in result]}
    return jsonify(data)

@bp.route('/api/revenue', methods=['GET'])
def revenue():
    # Example: return revenue per day (assume fixed price per vehicle)
    price_per_vehicle = 10
    from sqlalchemy import func
    result = db.session.query(func.date(Vehicle.exit_time), func.count(Vehicle.id)).filter(Vehicle.exit_time != None).group_by(func.date(Vehicle.exit_time)).all()
    data = {'labels': [str(r[0]) for r in result], 'values': [r[1]*price_per_vehicle for r in result]}
    return jsonify(data)

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logic'))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime

from database_connection import DatabaseConnection
from simulation import Simulation
from building import Building

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Flutter

db = DatabaseConnection()

_building = Building(name="ELEV8 Tower", floors=10, num_elevators=2, pending_requests=[])
_sim = Simulation(_building, tick_rate=1.0)
_sim.start_background()


@app.route('/sim')
def sim_dashboard():
    return render_template('sim.html')


@app.route('/client')
def client_panel():
    return render_template('client.html')


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()

        # Validate required fields
        if not data or 'campusID' not in data or 'password' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing campusID or password"
            }), 400

        campus_id = data.get('campusID')
        password = data.get('password')
        remember_me = data.get('rememberMe', False)

        # Validate password length
        if len(password) < 8:
            return jsonify({
                "status": "error",
                "message": "Password must be at least 8 characters long"
            }), 400

        # Look up user in the database
        user = db.get_user_by_campus_id(campus_id)

        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 401

        # Verify password against stored password (plain text comparison)
        if password != user['password']:
            return jsonify({
                "status": "error",
                "message": "Invalid password"
            }), 401

        # Login successful
        return jsonify({
            "status": "success",
            "message": "Login successful",
            "timestamp": datetime.now().isoformat(),
            "user": {
                "campusID": campus_id,
                "accessLevel": user['access_level'],
                "rememberMe": remember_me
            }
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during login: {str(e)}"
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    connected = db.connect()
    db.disconnect()
    return jsonify({
        "status": "healthy" if connected else "unhealthy",
        "database": "connected" if connected else "disconnected"
    }), 200 if connected else 503


@app.route('/api/elevator/call', methods=['POST'])
def elevator_call():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    current_floor = data.get('current_floor')
    destination_floor = data.get('destination_floor')
    access_level = data.get('access_level', 1)

    if current_floor is None or destination_floor is None:
        return jsonify({"status": "error", "message": "current_floor and destination_floor are required"}), 400

    if not isinstance(current_floor, int) or not isinstance(destination_floor, int):
        return jsonify({"status": "error", "message": "Floors must be integers"}), 400

    if current_floor == destination_floor:
        return jsonify({"status": "error", "message": "current_floor and destination_floor must differ"}), 400

    floors = _building.floors
    if not (0 <= current_floor < floors) or not (0 <= destination_floor < floors):
        return jsonify({"status": "error", "message": f"Floors must be between 0 and {floors - 1}"}), 400

    passenger_id = _sim.add_request(current_floor, destination_floor, access_level)
    return jsonify({
        "status": "success",
        "passenger_id": passenger_id,
        "message": f"Request queued. Passenger ID: {passenger_id}"
    }), 201


@app.route('/api/elevator/cancel', methods=['POST'])
def elevator_cancel():
    data = request.get_json()
    if not data or 'passenger_id' not in data:
        return jsonify({"status": "error", "message": "passenger_id is required"}), 400

    passenger_id = data.get('passenger_id')
    success, reason = _sim.cancel_request(passenger_id)

    if success:
        return jsonify({"status": "success", "message": f"Passenger {passenger_id} request cancelled"}), 200

    if reason == "already_boarded":
        return jsonify({
            "status": "error",
            "message": "Cannot cancel: passenger has already boarded an elevator"
        }), 409

    return jsonify({
        "status": "error",
        "message": f"Passenger {passenger_id} not found in waiting queue"
    }), 404


@app.route('/api/elevator/state', methods=['GET'])
def elevator_state():
    state = _sim.get_state()
    return jsonify({"status": "success", "state": state}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False, host='0.0.0.0')

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'logic'))

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from database_connection import DatabaseConnection
from simulation import Simulation
from building import Building
from live_mode import LiveModeManager

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Flutter

db = DatabaseConnection()

_DEFAULT_CONFIG = {
    "name": "ELEV8 Tower",
    "floors": 10,
    "num_elevators": 2,
    "elevator_capacity": 10,
    "seconds_per_floor": 1.0,
    "abandon_after_seconds": 90,
    "floor_access": {},            # {floor_int: min_access_level}
}

_config = dict(_DEFAULT_CONFIG)
_building = None
_sim = None
_live_mode = None


def _init_simulation(cfg):
    global _building, _sim, _live_mode
    if _live_mode is not None:
        _live_mode.stop()
    if _sim is not None:
        _sim.stop_background()
    _building = Building(
        name=cfg["name"],
        floors=cfg["floors"],
        num_elevators=cfg["num_elevators"],
        pending_requests=[],
        elevator_capacity=cfg["elevator_capacity"],
        floor_access=dict(cfg.get("floor_access", {})),
        abandon_after_seconds=cfg.get("abandon_after_seconds", 90),
    )
    _sim = Simulation(_building, seconds_per_floor=cfg["seconds_per_floor"])
    _sim.start_background()
    _live_mode = LiveModeManager(_sim)


_init_simulation(_config)


@app.route('/sim')
def sim_dashboard():
    return render_template('sim.html')


@app.route('/client')
def client_panel():
    return render_template('client.html')


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    connected = db.is_healthy()
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

    passenger_id, reason = _sim.add_request(current_floor, destination_floor, access_level)
    if passenger_id is None:
        return jsonify({"status": "error", "message": reason}), 403
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
    state['live_mode'] = _live_mode.get_status()
    return jsonify({"status": "success", "state": state}), 200


@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({"status": "success", "config": _config}), 200


@app.route('/api/config', methods=['POST'])
def set_config():
    global _config
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Missing request body"}), 400

    new_cfg = dict(_config)

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return jsonify({"status": "error", "message": "name must be a non-empty string"}), 400
        new_cfg["name"] = data["name"].strip()

    if "floors" in data:
        if not isinstance(data["floors"], int) or data["floors"] < 2:
            return jsonify({"status": "error", "message": "floors must be an integer >= 2"}), 400
        new_cfg["floors"] = data["floors"]

    if "num_elevators" in data:
        if not isinstance(data["num_elevators"], int) or data["num_elevators"] < 1:
            return jsonify({"status": "error", "message": "num_elevators must be an integer >= 1"}), 400
        new_cfg["num_elevators"] = data["num_elevators"]

    if "elevator_capacity" in data:
        if not isinstance(data["elevator_capacity"], int) or data["elevator_capacity"] < 1:
            return jsonify({"status": "error", "message": "elevator_capacity must be an integer >= 1"}), 400
        new_cfg["elevator_capacity"] = data["elevator_capacity"]

    if "seconds_per_floor" in data:
        try:
            seconds_per_floor = float(data["seconds_per_floor"])
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "seconds_per_floor must be a positive number"}), 400
        if seconds_per_floor <= 0:
            return jsonify({"status": "error", "message": "seconds_per_floor must be a positive number"}), 400
        new_cfg["seconds_per_floor"] = seconds_per_floor

    if "abandon_after_seconds" in data:
        try:
            t = float(data["abandon_after_seconds"])
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "abandon_after_seconds must be a number"}), 400
        if t < 0:
            return jsonify({"status": "error", "message": "abandon_after_seconds must be >= 0 (0 = never)"}), 400
        new_cfg["abandon_after_seconds"] = t

    if "floor_access" in data:
        fa = data["floor_access"]
        if not isinstance(fa, dict):
            return jsonify({"status": "error", "message": "floor_access must be an object"}), 400
        parsed = {}
        for k, v in fa.items():
            try:
                floor = int(k)
                level = int(v)
            except (TypeError, ValueError):
                return jsonify({"status": "error", "message": "floor_access keys and values must be integers"}), 400
            if not (0 <= floor < new_cfg["floors"]) or level < 0:
                return jsonify({"status": "error", "message": f"Invalid floor_access entry: floor {floor}"}), 400
            parsed[floor] = level
        new_cfg["floor_access"] = parsed

    _config = new_cfg
    _init_simulation(_config)
    return jsonify({"status": "success", "message": "Simulation reconfigured", "config": _config}), 200


@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    _init_simulation(_config)
    return jsonify({"status": "success", "message": "Simulation reset", "config": _config}), 200


_VALID_PATTERNS = LiveModeManager.VALID_PATTERNS


@app.route('/api/live-mode/start', methods=['POST'])
def live_mode_start():
    data = request.get_json() or {}
    rate             = data.get('rate_per_minute')
    pattern          = data.get('pattern')
    caf              = data.get('cafeteria_floor')
    inter_floor_pct  = data.get('inter_floor_pct')
    sim_start_hour   = data.get('sim_start_hour')
    sim_speed        = data.get('sim_speed')

    if rate is not None:
        try:
            rate = float(rate)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "rate_per_minute must be a number"}), 400
        if not (0.1 <= rate <= 120):
            return jsonify({"status": "error", "message": "rate_per_minute must be between 0.1 and 120"}), 400

    if pattern is not None and pattern not in _VALID_PATTERNS:
        return jsonify({"status": "error",
                        "message": f"pattern must be one of {sorted(_VALID_PATTERNS)}"}), 400

    if caf is not None:
        if not isinstance(caf, int) or not (0 <= caf < _building.floors):
            return jsonify({"status": "error",
                            "message": f"cafeteria_floor must be between 0 and {_building.floors - 1}"}), 400

    if inter_floor_pct is not None:
        try:
            inter_floor_pct = float(inter_floor_pct)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "inter_floor_pct must be a number"}), 400
        if not (0.0 <= inter_floor_pct <= 1.0):
            return jsonify({"status": "error", "message": "inter_floor_pct must be between 0.0 and 1.0"}), 400

    if sim_start_hour is not None:
        try:
            sim_start_hour = float(sim_start_hour)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "sim_start_hour must be a number"}), 400

    if sim_speed is not None:
        try:
            sim_speed = float(sim_speed)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "sim_speed must be a number"}), 400

    try:
        _live_mode.update(rate_per_minute=rate, pattern=pattern, cafeteria_floor=caf,
                          inter_floor_pct=inter_floor_pct,
                          sim_start_hour=sim_start_hour, sim_speed=sim_speed)
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    _live_mode.start()
    return jsonify({"status": "success", "message": "Live mode started",
                    "live_mode": _live_mode.get_status()}), 200


@app.route('/api/live-mode/stop', methods=['POST'])
def live_mode_stop():
    _live_mode.stop()
    return jsonify({"status": "success", "message": "Live mode stopped",
                    "live_mode": _live_mode.get_status()}), 200


@app.route('/api/live-mode/status', methods=['GET'])
def live_mode_status():
    return jsonify({"status": "success", "live_mode": _live_mode.get_status()}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False, host='0.0.0.0')

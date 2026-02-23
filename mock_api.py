from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import bcrypt
from database_connection import DatabaseConnection

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Flutter

db = DatabaseConnection()


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
        try:
            campus_id_int = int(campus_id)
        except (ValueError, TypeError):
            return jsonify({
                "status": "error",
                "message": "Campus ID must be a valid number"
            }), 400

        user = db.get_user_by_campus_id(campus_id_int)

        if not user:
            return jsonify({
                "status": "error",
                "message": "User not found"
            }), 401

        # Verify password against the stored bcrypt hash
        stored_hash = user['password'].encode('utf-8')
        password_bytes = password.encode('utf-8')

        if not bcrypt.checkpw(password_bytes, stored_hash):
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
                "campusID": campus_id_int,
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
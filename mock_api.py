from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

MOCK_RESPONSE = {
    "status": "success",
    "message": "Login successful",
    "timestamp": datetime.now().isoformat(),
    "user": {
        "campusID": None,
        "sessionToken": "mock_token_12345",
    }
}

@app.route('/api/login', methods = ['POST'])
def login():
    try:
        data = request.get_json()

        if not data or 'campusID' not in data or 'password' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing campusID or password"
            }), 400
        
        campusID = data.get('campusID')
        password = data.get('password')
        rememberMe = data.get('rememberMe', False)

        if len(password) < 8:
            return jsonify({
                "status": "error",
                "message": "Password must be at least 8 characters long"
            }), 400
        
        response = MOCK_RESPONSE.copy()
        response['user']['campusID'] = campusID
        response['user']['rememberMe'] = rememberMe

        return jsonify(response), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during login: {str(e)}"
        }), 500

@app.route('/health', methods = ['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
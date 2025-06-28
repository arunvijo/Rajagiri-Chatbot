# app.py

from flask import Flask, request, jsonify
from bot import handle_message

app = Flask(__name__)

@app.route("/")
def index():
    return "Rajagiri Chatbot Backend is live."

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or not message:
        return jsonify({"error": "Missing session_id or message"}), 400

    response = handle_message(session_id, message)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)

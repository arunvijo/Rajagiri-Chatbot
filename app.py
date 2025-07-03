"""Simplified Flask backend for Rajagiri Chatbot."""
from flask import Flask, render_template, request, jsonify
from chatbot import ask_rajagiri_bot
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Render the main chat interface."""
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Handle chat requests."""
    try:
        data = request.get_json(force=True)
        query = data.get("query", "").strip()
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Get response from chatbot
        answer, _ = ask_rajagiri_bot(query)
        
        return jsonify({
            "answer": answer,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
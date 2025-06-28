# app.py

from flask import Flask, request, jsonify
from google_cse import google_search

app = Flask(__name__)

@app.route("/")
def health():
    return "Rajagiri Chatbot API is running"

@app.route("/query", methods=["POST"])
def handle_query():
    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    results = google_search(query)
    return jsonify({
        "query": query,
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True)

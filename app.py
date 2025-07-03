from flask import Flask, render_template, request, jsonify, session
from chatbot import ask_rajagiri_bot
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "defaultsecret")

@app.route("/", methods=["GET"])
def index():
    history = session.get("history", [])
    return render_template("index.html", history=history)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    try:
        data = request.get_json(force=True)
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400

        answer, sources = ask_rajagiri_bot(query)

        # Save full chat history with sources displayed only on frontend
        history = session.get("history", [])
        history.append({"role": "user", "content": query})
        history.append({"role": "assistant", "content": answer, "sources": sources})
        session["history"] = history

        return jsonify({
            "answer": answer,
            "sources": sources,
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

@app.route("/clear", methods=["POST"])
def clear_history():
    session.pop("history", None)
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

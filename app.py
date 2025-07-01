"""Flask backend for Rajagiri Chatbot."""
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session

# import your pipeline
from chatbot import ask_rajagiri_bot

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-me")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []  # list of {role, content}

    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            # append user message
            session["history"].append({"role": "user", "content": question})

            # get bot answer
            answer, _ = ask_rajagiri_bot(question)
            session["history"].append({"role": "assistant", "content": answer})
            session.modified = True
        return redirect(url_for("index"))

    return render_template("index.html", history=session.get("history", []))

# ---- JSON endpoint (optional) ----
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    query = data.get("query", "")
    answer, sources = ask_rajagiri_bot(query)
    return jsonify({"answer": answer, "sources": sources})

if __name__ == "__main__":
    # local dev server (use Gunicorn in production)
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
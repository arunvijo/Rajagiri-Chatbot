"""Flask backend for Rajagiri Chatbot."""
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
import json
from datetime import datetime

# import your pipeline
from chatbot import ask_rajagiri_bot

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-me")
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 86400  # 1 day in seconds
Session(app)

# Initialize user data structure
def init_user_data():
    return {
        "chats": {},
        "current_chat": None,
        "user_info": None
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if "user_data" not in session:
        session["user_data"] = init_user_data()
    
    user_data = session["user_data"]

    # Pre-warm backend logic once per session
    if not session.get("warmed_up"):
        try:
            ask_rajagiri_bot("welcome")
        except Exception as e:
            print("Pre-warm failed:", e)
        session["warmed_up"] = True
        session.modified = True
    
    # Handle new chat creation
    if request.args.get("new") == "true":
        chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
        user_data["chats"][chat_id] = {
            "id": chat_id,
            "title": "New Chat",
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        user_data["current_chat"] = chat_id
        session.modified = True
        return redirect(url_for("index"))
    
    # Get current chat
    current_chat = user_data["current_chat"]
    chat_history = []
    
    if current_chat and current_chat in user_data["chats"]:
        chat_history = user_data["chats"][current_chat]["history"]
    
    if request.method == "POST":
        question = request.form.get("question", "").strip()
        if question:
            # Append user message
            chat_history.append({"role": "user", "content": question})
            
            # Get bot answer
            answer, _ = ask_rajagiri_bot(question)
            chat_history.append({"role": "assistant", "content": answer})
            
            # Update chat title if it's the first message
            if len(chat_history) == 2 and user_data["chats"][current_chat]["title"] == "New Chat":
                user_data["chats"][current_chat]["title"] = question[:50] + ("..." if len(question) > 50 else "")
            
            session.modified = True
        return redirect(url_for("index"))
    
    return render_template("index.html", 
                         history=chat_history,
                         chats=user_data["chats"],
                         current_chat=current_chat)


@app.route("/auth/google", methods=["POST"])
def auth_google():
    credential = request.json.get("credential")
    if not credential:
        return jsonify({"error": "No credential provided"}), 400
    
    # Verify the credential (you should implement proper verification)
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
        import google.auth.transport.requests
        
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        idinfo = id_token.verify_oauth2_token(credential, requests.Request(), CLIENT_ID)
        
        # Store user info in session
        if "user_data" not in session:
            session["user_data"] = init_user_data()
        
        session["user_data"]["user_info"] = {
            "id": idinfo["sub"],
            "name": idinfo["name"],
            "email": idinfo["email"],
            "picture": idinfo["picture"]
        }
        session.modified = True
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route("/chat/<chat_id>")
def load_chat(chat_id):
    if "user_data" not in session:
        session["user_data"] = init_user_data()
    
    user_data = session["user_data"]
    
    if chat_id in user_data["chats"]:
        user_data["current_chat"] = chat_id
        session.modified = True
    
    return redirect(url_for("index"))

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(force=True)
    query = data.get("query", "")
    answer, sources = ask_rajagiri_bot(query)
    return jsonify({"answer": answer, "sources": sources})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
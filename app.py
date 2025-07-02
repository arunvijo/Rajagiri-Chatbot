"""Flask backend for Rajagiri Chatbot."""
import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_session import Session
from datetime import datetime
from google.auth.transport import requests
from google.oauth2 import id_token
import traceback

# Import your pipeline
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
    """Main route handling both GET and POST requests"""
    try:
        # Initialize session data if not exists
        if "user_data" not in session:
            session["user_data"] = init_user_data()
        
        user_data = session["user_data"]

        # Pre-warm backend logic once per session
        if not session.get("warmed_up"):
            try:
                ask_rajagiri_bot("welcome")
            except Exception as e:
                app.logger.error(f"Pre-warm failed: {str(e)}")
            session["warmed_up"] = True
            session.modified = True

        # Handle new chat creation
        if request.args.get("new") == "true":
            return create_new_chat(user_data)

        # Handle POST request (form submission)
        if request.method == "POST":
            return handle_chat_message(user_data)

        # Prepare data for template rendering
        current_chat = user_data["current_chat"]
        chat_history = []
        
        if current_chat and current_chat in user_data["chats"]:
            chat_history = user_data["chats"][current_chat]["history"]
        
        return render_template("index.html", 
                            history=chat_history,
                            chats=user_data["chats"],
                            current_chat=current_chat,
                            user_data=user_data)

    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}\n{traceback.format_exc()}")
        return render_template("error.html",
                            error="An error occurred while processing your request",
                            user_data=session.get("user_data", init_user_data())), 500

def create_new_chat(user_data):
    """Helper function to create a new chat"""
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

def handle_chat_message(user_data):
    """Helper function to handle chat messages"""
    question = request.form.get("question", "").strip()
    if not question:
        return redirect(url_for("index"))
    
    current_chat = user_data["current_chat"]
    if not current_chat or current_chat not in user_data["chats"]:
        return redirect(url_for("index"))

    # Append user message
    user_data["chats"][current_chat]["history"].append({
        "role": "user",
        "content": question
    })
    
    # Get bot answer
    try:
        answer, _ = ask_rajagiri_bot(question)
    except Exception as e:
        app.logger.error(f"Error getting bot response: {str(e)}")
        answer = "Sorry, I encountered an error processing your request."

    # Append bot response
    user_data["chats"][current_chat]["history"].append({
        "role": "assistant",
        "content": answer
    })
    
    # Update chat title if first message
    if len(user_data["chats"][current_chat]["history"]) == 2:
        user_data["chats"][current_chat]["title"] = question[:50] + ("..." if len(question) > 50 else "")
    
    session.modified = True
    return redirect(url_for("index"))

@app.route("/auth/google", methods=["POST"])
def auth_google():
    """Handle Google authentication"""
    credential = request.json.get("credential")
    if not credential:
        return jsonify({"error": "No credential provided"}), 400
    
    try:
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not CLIENT_ID:
            raise ValueError("Google Client ID not configured")
        
        idinfo = id_token.verify_oauth2_token(credential, requests.Request(), CLIENT_ID)
        
        if "user_data" not in session:
            session["user_data"] = init_user_data()
        
        session["user_data"]["user_info"] = {
            "id": idinfo["sub"],
            "name": idinfo["name"],
            "email": idinfo["email"],
            "picture": idinfo["picture"]
        }
        session.modified = True
        
        return jsonify({
            "status": "success",
            "user": {
                "name": idinfo["name"],
                "picture": idinfo["picture"]
            }
        })
    except Exception as e:
        app.logger.error(f"Google auth error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Authentication failed"}), 401

@app.route("/chat/<chat_id>")
def load_chat(chat_id):
    """Load a specific chat"""
    if "user_data" not in session:
        session["user_data"] = init_user_data()
    
    user_data = session["user_data"]
    
    if chat_id in user_data["chats"]:
        user_data["current_chat"] = chat_id
        session.modified = True
    
    return redirect(url_for("index"))

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """API endpoint for chat"""
    try:
        data = request.get_json(force=True)
        query = data.get("query", "")
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        answer, sources = ask_rajagiri_bot(query)
        return jsonify({
            "answer": answer,
            "sources": sources,
            "status": "success"
        })
    except Exception as e:
        app.logger.error(f"API chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/rate-message", methods=["POST"])
def rate_message():
    """Handle message rating"""
    if "user_data" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        chat_id = data.get("chatId")
        message_index = data.get("messageIndex")
        action = data.get("action")
        
        if not all([chat_id, message_index, action]):
            return jsonify({"error": "Missing parameters"}), 400
        
        message_index = int(message_index)
        user_data = session["user_data"]
        chat = user_data["chats"].get(chat_id)
        
        if not chat or message_index >= len(chat["history"]):
            return jsonify({"error": "Invalid chat or message"}), 404
        
        # Initialize ratings if not exists
        if "ratings" not in chat:
            chat["ratings"] = {}
        
        chat["ratings"][str(message_index)] = action
        session.modified = True
        
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Rate message error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/new-chat", methods=["POST"])
def new_chat():
    """Create a new chat"""
    if "user_data" not in session:
        session["user_data"] = init_user_data()
    
    try:
        chat_id = datetime.now().strftime("%Y%m%d%H%M%S")
        session["user_data"]["chats"][chat_id] = {
            "id": chat_id,
            "title": "New Chat",
            "history": [],
            "created_at": datetime.now().isoformat()
        }
        session["user_data"]["current_chat"] = chat_id
        session.modified = True
        
        return jsonify({
            "status": "success",
            "chat_id": chat_id,
            "redirect": url_for("index")
        })
    except Exception as e:
        app.logger.error(f"New chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Failed to create new chat"}), 500

@app.route("/delete-chat/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    """Delete a chat"""
    if "user_data" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        user_data = session["user_data"]
        
        if chat_id not in user_data["chats"]:
            return jsonify({"error": "Chat not found"}), 404
        
        # Handle current chat reassignment
        if user_data["current_chat"] == chat_id:
            remaining_chats = [cid for cid in user_data["chats"].keys() if cid != chat_id]
            user_data["current_chat"] = remaining_chats[0] if remaining_chats else None
        
        del user_data["chats"][chat_id]
        session.modified = True
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Delete chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/rename-chat/<chat_id>", methods=["PUT"])
def rename_chat(chat_id):
    """Rename a chat"""
    if "user_data" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        new_title = request.json.get("title")
        if not new_title:
            return jsonify({"error": "Title is required"}), 400
        
        user_data = session["user_data"]
        
        if chat_id not in user_data["chats"]:
            return jsonify({"error": "Chat not found"}), 404
        
        user_data["chats"][chat_id]["title"] = new_title[:50]  # Limit title length
        session.modified = True
        return jsonify({
            "status": "success",
            "new_title": new_title[:50]
        })
    except Exception as e:
        app.logger.error(f"Rename chat error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/auth/logout", methods=["POST"])
def logout():
    """Handle user logout"""
    try:
        session.clear()
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f"Logout error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Logout failed"}), 500

@app.route("/auth/check")
def check_auth():
    """Check authentication status"""
    try:
        if "user_data" not in session:
            session["user_data"] = init_user_data()
        
        user_data = session["user_data"]
        authenticated = bool(user_data.get("user_info"))
        
        return jsonify({
            "authenticated": authenticated,
            "user": user_data.get("user_info", {})
        })
    except Exception as e:
        app.logger.error(f"Auth check error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template("error.html",
                         error="Page not found",
                         user_data=session.get("user_data", init_user_data())), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template("error.html",
                         error="Internal server error",
                         user_data=session.get("user_data", init_user_data())), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
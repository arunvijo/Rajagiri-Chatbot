# bot.py

from memory import sessions, ChatSession
from google_cse import google_search
from scraper import scrape_text_from_url
from rag_parser import find_answer

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = ChatSession()
    return sessions[session_id]

def handle_message(session_id, message):
    session = get_session(session_id)
    msg = message.lower().strip()

    if msg in {"hi", "hello", "hey"}:
        return "Hi there! I'm the Rajagiri Assistant. How can I help you?"

    if "admission" in msg and not session.context:
        session.context = "admission"
        session.awaiting_clarification = True
        return "Are you asking about BTech or MTech admission?"

    if session.awaiting_clarification:
        if "btech" in msg:
            session.subtopic = "btech"
        elif "mtech" in msg:
            session.subtopic = "mtech"
        else:
            return "Please tell me if it's BTech or MTech you're interested in."

        # Search Google CSE
        query = f"{session.subtopic} admission 2025 rajagiritech"
        session.results = google_search(query)

        # Scrape top 3 results
        session.scraped_texts = []
        for r in session.results:
            text = scrape_text_from_url(r["link"])
            session.scraped_texts.append(text)

        session.awaiting_clarification = False
        return f"Great! You can now ask about {session.subtopic.upper()} admission 2025."

    # Try answering using scraped content
    if session.scraped_texts:
        answer = find_answer(session.scraped_texts, msg)
        if answer:
            return answer
        else:
            return "I couldn’t find a direct answer in the admission pages. You can also check:\n" + \
                "\n".join([r['link'] for r in session.results])

    return "I'm not sure how to help. Try asking about admissions, departments, or contact info."

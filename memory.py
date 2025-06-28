# memory.py

class ChatSession:
    def __init__(self):
        self.context = None
        self.subtopic = None
        self.results = []           # Top 3 CSE results
        self.scraped_texts = []     # Scraped full-page content from each result
        self.awaiting_clarification = False

sessions = {}

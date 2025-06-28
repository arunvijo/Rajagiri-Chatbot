# memory.py

class ChatSession:
    def __init__(self):
        self.context = None        # e.g., "admission"
        self.subtopic = None       # e.g., "btech"
        self.results = []          # top 3 search results
        self.awaiting_clarification = False

# Keep all sessions here (in-memory)
sessions = {}

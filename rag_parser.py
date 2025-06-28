# rag_parser.py

def find_answer(texts, query):
    query = query.lower()
    for text in texts:
        if query in text.lower():
            start = text.lower().find(query)
            snippet = text[start:start+300]
            return snippet + "..."
    return None

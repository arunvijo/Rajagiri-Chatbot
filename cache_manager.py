# cache_manager.py
import json
import os
from typing import Optional, Dict

CACHE_FILE = "query_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        CACHE = json.load(f)
else:
    CACHE = {}

def get_cached_answer(query: str) -> Optional[Dict]:
    return CACHE.get(query.strip().lower())

def store_cached_answer(query: str, answer_data: Dict):
    key = query.strip().lower()
    CACHE[key] = answer_data
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(CACHE, f, indent=2)
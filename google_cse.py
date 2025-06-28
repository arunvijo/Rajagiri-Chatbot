import requests
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from typing import List, Dict
import time
import logging

logger = logging.getLogger(__name__)

def google_search(
    query: str,
    num: int = 3,
    site_restriction: str = "rajagiritech.ac.in,rajagiri.edu"
) -> List[Dict]:
    """Search restricted to Rajagiri College domains"""
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": f"{query} site:{site_restriction}",
        "num": min(num, 10),
        "lr": "lang_en",
        "sort": "date"  # Prefer newer content
    }
    
    try:
        res = requests.get(url, params=params, timeout=15)
        res.raise_for_status()
        data = res.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []

def search_rajagiri_resources(query: str, num: int = 3) -> List[Dict]:
    """Search official Rajagiri College resources"""
    # First try with strict site restriction
    results = google_search(query, num=num)
    
    # If no results, try relaxing the query but keep site restriction
    if not results:
        simplified_query = ' '.join([word for word in query.split() if len(word) > 3])
        if simplified_query:
            results = google_search(simplified_query, num=num)
    
    return results
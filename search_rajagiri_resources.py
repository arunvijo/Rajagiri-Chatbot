"""Google Programmable Search wrapper – tuned for Rajagiri."""
from __future__ import annotations

import os
import requests
from functools import lru_cache
from typing import List, Dict

from dotenv import load_dotenv

load_dotenv()

API_KEY: str | None = os.getenv("GOOGLE_API_KEY")      # keep in .env
CX_ID:   str | None = os.getenv("GOOGLE_CSE_ID", "24db28382bbc14aec")

BASE_URL = "https://www.googleapis.com/customsearch/v1"


@lru_cache(maxsize=128)
def google_search(query: str, *, num_results: int = 8) -> List[Dict[str, str]]:
    """Return top N results (title, link, snippet) from the Rajagiri CSE.

    The CX is already locked to the domain, so no siteSearch param needed.
    """
    if not API_KEY or not CX_ID:
        raise RuntimeError("Google API key or CX ID missing – check .env")

    params = {
        "key": API_KEY,
        "cx": CX_ID,
        "q": query,
        "num": num_results,
        "safe": "active",   # extra safety
    }

    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    return [
        {
            "title":   item.get("title", ""),
            "link":    item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in data.get("items", [])
    ]
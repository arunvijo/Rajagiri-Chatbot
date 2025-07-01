"""Grab & clean visible text from a webpage (basic heuristic)."""
from __future__ import annotations

import re, requests
from bs4 import BeautifulSoup
from functools import lru_cache

USER_AGENT = {
    "User‑Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123 Safari/537.36"
    )
}

BLOCK_TAGS = ["script", "style", "noscript", "header", "footer", "svg", "img", "form"]

@lru_cache(maxsize=128)
def scrape_clean_text(url: str, *, char_limit: int = 8_000) -> str:
    """Return minified visible text (UTF‑8) limited to *char_limit* chars."""
    try:
        r = requests.get(url, headers=USER_AGENT, timeout=15)
        r.raise_for_status()
    except Exception:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(BLOCK_TAGS):
        tag.decompose()

    text = re.sub(r"\s+", " ", soup.get_text(" ").strip())
    return text[:char_limit]
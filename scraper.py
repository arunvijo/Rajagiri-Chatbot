# scraper.py

import requests
from bs4 import BeautifulSoup

def scrape_text_from_url(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for script in soup(["script", "style", "footer", "nav"]):
            script.extract()
        text = soup.get_text(separator=' ', strip=True)
        return ' '.join(text.split())
    except Exception:
        return ""

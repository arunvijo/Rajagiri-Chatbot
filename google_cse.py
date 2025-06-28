# google_cse.py

import requests
from config import API_KEY, CSE_ID

def google_search(query, num_results=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": API_KEY,
        "cx": CSE_ID,
        "num": num_results
    }

    response = requests.get(url, params=params)
    results = []

    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            })
    else:
        results.append({
            "title": "Error",
            "link": "",
            "snippet": f"Status: {response.status_code}, {response.text}"
        })

    return results

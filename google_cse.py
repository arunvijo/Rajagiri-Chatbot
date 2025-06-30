import requests
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class GoogleSearchError(Exception):
    """Custom exception for Google Search API errors"""
    pass

def google_search( # This function MUST be lowercase as 'google_search'
    query: str,
    num: int = 3,
    site_restriction: Optional[str] = None,
    max_retries: int = 2,
    retry_delay: float = 1.0
) -> List[Dict]:
    """
    Enhanced Google Custom Search API wrapper with:
    - Better error handling
    - Retry mechanism
    - Site restriction option
    - Type hints
    """
    url = "https://www.googleapis.com/customsearch/v1"
    
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": min(num, 10),  # Google CSE max is 10 results per request
        "lr": "lang_en"  # Language restriction (English)
    }
    
    # Apply site restriction directly to params for better specificity
    if site_restriction:
        params["siteSearch"] = site_restriction
        # IMPORTANT: The 'siteSearchFilter' parameter has been REMOVED as it was causing the 400 Bad Request.
        # Do not re-add it unless you fully understand its very specific usage (which is not for rich snippets here).
    
    headers = {
        "User-Agent": "RajagiriCollegeBot/1.0"
    }

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempt {attempt+1}: Searching Google CSE for '{query}' with site restriction '{site_restriction}'")
            res = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=15  # Increased timeout
            )
            
            if res.status_code == 429:
                if attempt < max_retries:
                    logger.warning(f"Rate limit hit. Retrying in {retry_delay * (attempt + 1)}s...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise GoogleSearchError("Google API rate limit exceeded")
            
            res.raise_for_status() # This will raise an exception for 4xx/5xx responses (e.g., 400, 403, 404, 500)
            
            data = res.json()
            
            if "error" in data:
                # If Google returns a JSON error, raise it
                raise GoogleSearchError(data["error"].get("message", "Unknown Google API error"))
            
            return data.get("items", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google API request failed on attempt {attempt+1}: {str(e)}")
            if attempt == max_retries:
                # Only raise the final error after all retries are exhausted
                raise GoogleSearchError(f"Google API request failed after {max_retries+1} attempts: {str(e)}")
            time.sleep(retry_delay * (attempt + 1))
    
    return [] # This line should technically not be reached if max_retries is handled with raise

def search_rajagiri_resources(query: str, num: int = 3) -> List[Dict]:
    """
    Specialized search for Rajagiri College resources with strict domain focus.
    Prioritizes rajagiritech.ac.in.
    """
    rajagiri_domains = "rajagiritech.ac.in,rajagiri.edu" # Keep both if rajagiri.edu is also official
    
    try:
        # Strictly search within Rajagiri domains by calling the lowercase google_search function
        results = google_search( 
            query,
            num=num,
            site_restriction=rajagiri_domains
        )
        
        return results
        
    except GoogleSearchError as e:
        logger.error(f"Search error in search_rajagiri_resources: {e}")
        return []

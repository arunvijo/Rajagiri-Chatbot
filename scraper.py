import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def scrape_clean_text(url: str, max_depth: int = 0) -> Optional[str]:
    """Enhanced scraper focused on Rajagiri College website structure"""
    try:
        headers = {
            "User-Agent": "RajagiriCollegeBot/1.0 (+https://www.rajagiritech.ac.in)"
        }
        
        res = requests.get(url, timeout=15, headers=headers)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Remove unwanted elements common in college websites
        for tag in soup(['script', 'style', 'footer', 'nav', 'header', 
                        'aside', 'iframe', 'form', 'button', 'img']):
            tag.decompose()
        
        # Try to find main content area - common patterns in college sites
        main_content = (soup.find('main') or 
                       soup.find('article') or 
                       soup.find('div', {'id': 'content'}) or
                       soup.find('div', {'class': 'content-area'}) or
                       soup)
        
        # Extract text with structure preservation
        text_parts = []
        
        # Special handling for common college page structures
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'table']):
            if element.name.startswith('h'):
                text_parts.append(f"\n\n{element.get_text().upper()}\n")
            elif element.name == 'table':
                # Handle tables common in course descriptions
                rows = []
                for row in element.find_all('tr'):
                    cells = [cell.get_text(' ', strip=True) for cell in row.find_all(['th', 'td'])]
                    rows.append(' | '.join(cells))
                text_parts.append('\n'.join(rows))
            else:
                text = element.get_text(' ', strip=True)
                if len(text.split()) > 2:  # Only include meaningful text
                    text_parts.append(text)
        
        main_text = ' '.join(text_parts)
        main_text = re.sub(r'\s+', ' ', main_text).strip()
        
        return main_text if main_text else None
        
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None
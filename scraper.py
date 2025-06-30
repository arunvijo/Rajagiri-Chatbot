import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging

logger = logging.getLogger(__name__)

def is_internal_link(url: str, base_url: str) -> bool:
    """Check if a link is internal to the same domain"""
    # More robust check for relative URLs and domain matching
    return url.startswith(base_url) or (not url.startswith(('http://', 'https://')) and not url.startswith('javascript:'))

def scrape_clean_text(url: str, max_pages: int = 1) -> str:
    """Enhanced scraper that can follow internal links for more context,
    focusing on relevant content and handling common Rajagiri structures."""
    try:
        base_url = '/'.join(url.split('/')[:3])
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        res = requests.get(url, timeout=15, headers=headers)
        if res.status_code != 200:
            logger.warning(f"Failed to fetch {url} with status code {res.status_code}")
            return ""
        
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Remove unwanted elements more aggressively but carefully
        for tag in soup(['script', 'style', 'footer', 'nav', 'header', 'aside', 
                         'iframe', 'noscript', 'form', 'button', 'img', 'svg',
                         'meta', 'link', 'input', 'select', 'textarea']): # Added more form/meta tags
            tag.decompose()
        
        # Try to identify common main content areas specific to websites like Rajagiri's
        # This might need tuning based on actual Rajagiri page structures.
        main_content_selectors = [
            'div#ContentPlaceHolder1_UpdatePanel1', # Common ASP.NET content placeholder
            'div.main-content',
            'div.container-fluid',
            'div.page-content',
            'main', 'article',
            'div[role="main"]',
            'div[itemprop="articleBody"]',
            'div.col-md-9', # Common for a main content column in a grid layout
            'div.col-lg-8'
        ]
        
        main_content = None
        for selector in main_content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no specific content area found, fall back to body but remove some common non-content divs
        if not main_content:
            main_content = soup.body
            if main_content:
                for unwanted_class in ['navbar', 'header', 'footer', 'sidebar', 'widget', 'menu', 'breadcrumb']:
                    for div in main_content.find_all('div', class_=re.compile(f'.*{unwanted_class}.*', re.IGNORECASE)):
                        div.decompose()
                # Also remove any elements commonly found outside main content but not in specific headers/footers
                for div in main_content.find_all('div', id=re.compile(r'(?:banner|slider|carousel|ads|promo)')):
                    div.decompose()

        if not main_content:
            main_content = soup # Fallback to entire soup if no main content identified

        # Extract text with better structure and clean up
        text_parts = []
        for element in main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'span']): # Added span
            element_text = element.get_text(' ', strip=True)
            if element_text: # Ensure text is not empty
                # Preserve headings and add extra newlines for readability
                if element.name.startswith('h'):
                    text_parts.append(f"\n\n{element_text.upper()}\n")
                elif element.name == 'li':
                    text_parts.append(f"- {element_text}") # Bullet points for list items
                else:
                    text_parts.append(element_text)
        
        main_text = ' '.join(text_parts)
        main_text = re.sub(r'\s+', ' ', main_text).strip()
        main_text = re.sub(r'\n\s*\n', '\n\n', main_text) # Collapse multiple newlines

        # Optionally follow internal links to get more context
        # Be cautious with max_pages > 1 to avoid excessive scraping and irrelevant info.
        # For a college chatbot, focusing on 1-2 highly relevant pages is often better.
        if max_pages > 1:
            internal_links = set()
            for link in main_content.find_all('a', href=True): # Only follow links within the main content
                href = link['href']
                full_url = urljoin(base_url, href)
                # Ensure the link is clean, internal, and not pointing to the same page or anchors
                if is_internal_link(full_url, base_url) and full_url != url and '#' not in full_url and not full_url.endswith(('.pdf', '.doc', '.docx')):
                    internal_links.add(full_url)
            
            # Follow up to max_pages-1 internal links (prioritize based on text in link)
            # You might want to add a heuristic here to prioritize links that contain keywords from the query.
            for i, link in enumerate(sorted(list(internal_links))[:max_pages-1]): # Sorting for consistent behavior
                try:
                    logger.info(f"Scraping linked page: {link}")
                    link_res = requests.get(link, timeout=10, headers=headers)
                    if link_res.status_code == 200:
                        link_soup = BeautifulSoup(link_res.content, 'html.parser')
                        link_text_parts_linked = []
                        # Extract main content from linked page as well
                        linked_main_content = link_soup.find('main') or link_soup.find('article') or link_soup.find('div', class_=re.compile('content|main')) or link_soup.body
                        if linked_main_content:
                            for element in linked_main_content.find_all(['p', 'h1', 'h2', 'h3', 'li']):
                                element_text = element.get_text(' ', strip=True)
                                if element_text:
                                    link_text_parts_linked.append(element_text)
                        
                        link_text = ' '.join(link_text_parts_linked)
                        link_text = re.sub(r'\s+', ' ', link_text).strip()
                        main_text += f"\n\n--- Related Content from {link} ---\n{link_text[:4000]}" # Limit linked content to prevent bloat
                except Exception as e:
                    logger.warning(f"Error scraping linked page {link}: {e}")
                    continue
        
        return main_text
    
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return ""
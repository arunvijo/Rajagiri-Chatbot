from langchain.docstore.document import Document
from google_cse import search_rajagiri_resources
from scraper import scrape_clean_text
from openai import OpenAI
import re
from typing import List, Dict, Optional
import time
from config import OPENROUTER_API_KEY
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Official Rajagiri College domains
RAJAGIRI_DOMAINS = [
    'rajagiritech.ac.in',
    'rajagiri.edu',
    'www.rajagiritech.ac.in',
    'www.rajagiri.edu'
]

class ChatbotResponse:
    """Container for chatbot response with additional metadata"""
    def __init__(self, answer: str, sources: List[str], is_confident: bool):
        self.answer = answer
        self.sources = sources
        self.is_confident = is_confident

def is_official_source(url: str) -> bool:
    """Check if URL belongs to official Rajagiri domains"""
    try:
        domain = urlparse(url).netloc
        return any(domain.endswith(d) for d in RAJAGIRI_DOMAINS)
    except:
        return False

def clean_text(text: str) -> str:
    """Enhanced text cleaning for college website content"""
    # Remove special characters but preserve basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-–—\'"()\[\]{}]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common website artifacts
    text = re.sub(r'(Home|About|Contact|Sitemap|Privacy Policy)\s*\|?\s*', '', text, flags=re.I)
    return text

def extract_admission_content(content: str) -> str:
    """Specialized extraction for admission-related content"""
    # Look for common admission section patterns
    patterns = [
        r'admission\s+(process|procedure|requirements|dates)',
        r'how\s+to\s+apply',
        r'eligibility\s+criteria',
        r'application\s+form',
        r'important\s+dates'
    ]
    
    sections = []
    lines = content.split('\n')
    current_section = []
    in_relevant_section = False
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check for section headers
        is_header = (line_clean.isupper() and len(line_clean.split()) < 8) or \
                   re.match(r'^(#+|==+|--+|\*+|•|\d+\.)\s+', line_clean)
        
        # Check for admission keywords
        has_keyword = any(re.search(pattern, line_clean, re.I) for pattern in patterns)
        
        if is_header or has_keyword:
            if current_section:
                sections.append(' '.join(current_section))
                current_section = []
            in_relevant_section = True
            
        if in_relevant_section:
            current_section.append(line_clean)
            if len(current_section) > 15:  # Limit section length
                sections.append(' '.join(current_section))
                current_section = []
                in_relevant_section = False
    
    if current_section:
        sections.append(' '.join(current_section))
    
    return '\n\n'.join(sections)[:10000]

def generate_response_prompt(query: str, context: str) -> str:
    """Construct a strict prompt forcing website-based answers"""
    return f"""You are RajagiriBot, the official AI assistant for Rajagiri College. 
You must answer questions STRICTLY based on the provided context from the college website.

Guidelines:
1. Only use information from the provided context
2. Be precise and factual
3. For admission queries, include steps, dates, requirements
4. For courses, mention duration, eligibility, specializations
5. Never invent information - say "I couldn't find" if unsure
6. Format clearly with bullet points when appropriate

Question: {query}

Website Context:
{context}

Provide a concise, accurate answer based ONLY on the above context:"""

def run_openrouter_llm(prompt: str) -> str:
    """Run query through LLM with strict constraints"""
    try:
        response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[{
                "role": "system",
                "content": "You are an assistant that strictly answers using only the provided content from Rajagiri College's website."
            }, {
                "role": "user", 
                "content": prompt
            }],
            temperature=0.1,  # Very low for factual accuracy
            max_tokens=1000
        )
        return clean_text(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return "I'm having technical difficulties. Please try again later."

def process_search_results(results: List[Dict], query: str) -> List[Document]:
    """Process results into documents with relevant content"""
    docs = []
    for result in results:
        try:
            url = result['link']
            if not is_official_source(url):
                continue
                
            logger.info(f"Processing official source: {url}")
            content = scrape_clean_text(url)
            if not content:
                continue
                
            # Special handling for admission queries
            if 'admission' in query.lower() or 'apply' in query.lower():
                relevant_content = extract_admission_content(content)
            else:
                relevant_content = extract_relevant_sections(content, query)
                
            if relevant_content:
                docs.append(Document(
                    page_content=relevant_content,
                    metadata={
                        "source": url,
                        "title": result.get('title', url),
                        "last_updated": time.strftime("%Y-%m-%d")
                    }
                ))
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            continue
            
    return docs

def answer_query_with_langchain(query: str) -> ChatbotResponse:
    """Main function to answer queries using only website content"""
    logger.info(f"Processing query: {query}")
    
    # Step 1: Search official college resources
    search_results = search_rajagiri_resources(query, num=5)
    if not search_results:
        return ChatbotResponse(
            "I couldn't access Rajagiri's official resources currently. "
            "Please visit https://www.rajagiritech.ac.in directly for information.",
            [],
            False
        )
    
    # Step 2: Process and filter results
    docs = process_search_results(search_results, query)
    if not docs:
        return ChatbotResponse(
            "I couldn't find specific information about that on Rajagiri's official website. "
            "You might want to check the relevant department page or contact the administration.",
            [],
            False
        )
    
    # Step 3: Prioritize documents
    docs.sort(key=lambda x: (
        -sum(1 for term in query.lower().split() if term in x.metadata['title'].lower()),
        -len(x.page_content)
    ))
    
    # Step 4: Build context from top 3 most relevant pages
    context_parts = []
    sources = set()
    total_length = 0
    
    for doc in docs[:3]:
        source_info = f"Source: {doc.metadata['title']} ({doc.metadata['source']})"
        doc_content = f"{source_info}\nContent:\n{doc.page_content}\n\n"
        
        if total_length + len(doc_content) > 8000:  # Context window limit
            break
            
        context_parts.append(doc_content)
        sources.add(doc.metadata['source'])
        total_length += len(doc_content)
    
    combined_context = "\n".join(context_parts)
    
    # Step 5: Generate response
    prompt = generate_response_prompt(query, combined_context)
    answer = run_openrouter_llm(prompt)
    
    # Step 6: Verify answer quality
    is_confident = not any(phrase in answer.lower() for phrase in [
        "i couldn't find",
        "not mentioned",
        "not specified",
        "not provided"
    ])
    
    # Add sources if we have a confident answer
    if is_confident and sources:
        answer += "\n\nFor official information, visit:\n- " + "\n- ".join(sources)
    
    return ChatbotResponse(
        answer=answer,
        sources=list(sources),
        is_confident=is_confident
    )

def answer_query(query: str) -> str:
    """Public interface for the chatbot"""
    response = answer_query_with_langchain(query)
    
    # If not confident, suggest specific pages to visit
    if not response.is_confident and 'admission' in query.lower():
        return response.answer + "\n\nYou may want to check the Admission section at: https://www.rajagiritech.ac.in/home/admission.asp"
    
    return response.answer
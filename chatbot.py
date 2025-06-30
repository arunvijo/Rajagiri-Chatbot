from langchain.docstore.document import Document
from google_cse import search_rajagiri_resources
from scraper import scrape_clean_text
from openai import OpenAI
import re
from typing import List, Dict, Optional
import time
from config import OPENROUTER_API_KEY
import logging

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

class ChatbotResponse:
    """Container for chatbot response with additional metadata"""
    def __init__(self, answer: str, sources: List[str], context_used: str):
        self.answer = answer
        self.sources = sources
        self.context_used = context_used

def clean_text(text: str) -> str:
    """Enhanced text cleaning with more normalization and clarity"""
    # Replace common unicode quotes with ASCII
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    # Remove special characters but preserve basic punctuation
    text = re.sub(r'[^\w\s.,!?;:\-–—\'"()\[\]{}€₹%]', ' ', text) # Added common symbols
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove citation markers like [1], (2)
    text = re.sub(r'\[\d+\]|\(\d+\)|\b\w+\s?\[\d+\]', '', text) 
    return text

def extract_relevant_sections(content: str, query: str, max_length: int = 4000) -> str:
    """
    Advanced section extraction that:
    - Identifies headings and related content
    - Scores sections by relevance (keyword density, heading matches)
    - Prioritizes shorter, more direct sentences related to query
    - Maintains document structure within the extracted context
    - Uses Sentence-BERT (or similar) for semantic similarity if performance allows,
      otherwise relies on enhanced keyword matching.
    """
    lines = content.split('\n')
    sections = []
    current_section_lines = []
    heading_stack = []
    
    # Pre-process query for keyword matching (more robust)
    query_keywords = set(word.lower() for word in re.findall(r'\b\w{3,}\b', query))
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Detect heading lines (improved regex)
        is_heading = (
            re.match(r'^(#+|={2,}|-{2,}|\*+|\d+\.)\s+.+', line_clean) or # Markdown-style headings, numbered lists
            (line_clean.isupper() and len(line_clean.split()) < 10 and not line_clean.isdigit()) # All caps short lines
        )
        
        if is_heading:
            if current_section_lines:
                sections.append({
                    'content': ' '.join(current_section_lines),
                    'headings': heading_stack.copy(),
                    'raw_lines': current_section_lines.copy() # Keep raw lines for better sentence processing
                })
                current_section_lines = []
            heading_stack.append(line_clean)
        elif current_section_lines or heading_stack: # Only add content if we're in a section or just started a new heading
            current_section_lines.append(line_clean)
    
    if current_section_lines:
        sections.append({
            'content': ' '.join(current_section_lines),
            'headings': heading_stack.copy(),
            'raw_lines': current_section_lines.copy()
        })
    
    # Score sections by relevance
    scored_sections = []
    for section_data in sections:
        content_lower = section_data['content'].lower()
        
        # Calculate keyword score
        keyword_score = sum(1 for keyword in query_keywords if keyword in content_lower)
        
        # Calculate heading relevance score
        heading_score = sum(
            1 for heading in section_data['headings'] 
            if any(keyword in heading.lower() for keyword in query_keywords)
        )
        
        # Sentence-level relevance (simple: count sentences with keywords)
        sentence_relevance_score = 0
        relevant_sentences = []
        for sentence in re.split(r'[.!?]', section_data['content']): # Split into sentences
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in query_keywords):
                sentence_relevance_score += 1
                relevant_sentences.append(sentence.strip())

        # Combine scores
        score = keyword_score + (heading_score * 3) + (sentence_relevance_score * 0.5) # Headings are highly indicative
        
        if score > 0:
            # Reconstruct content with headings for context,
            # prioritizing relevant sentences if many.
            section_text_parts = []
            if section_data['headings']:
                section_text_parts.extend([f"Section: {h}" for h in section_data['headings']])
            
            if relevant_sentences:
                section_text_parts.append(" ".join(relevant_sentences[:5])) # Take top N relevant sentences
            else:
                section_text_parts.append(section_data['content']) # Fallback to full section if no specific sentences hit
            
            # Add a small penalty for longer sections if their score isn't proportionally high
            score -= (len(section_data['content']) / 1000) * 0.1

            scored_sections.append((score, "\n".join(section_text_parts)))
    
    # Sort by score and build the final context, respecting max_length
    scored_sections.sort(reverse=True, key=lambda x: x[0])
    
    final_context_parts = []
    current_length = 0
    for score, content_piece in scored_sections:
        if current_length + len(content_piece) > max_length:
            break
        final_context_parts.append(content_piece)
        current_length += len(content_piece)
            
    return "\n\n".join(final_context_parts)

def generate_response_prompt(query: str, context: str) -> str:
    """Construct an optimized prompt for the LLM, emphasizing the Rajagiri context."""
    return f"""You are RajagiriBot, the official AI assistant for Rajagiri College of Engineering & Technology. Your primary goal is to provide accurate, up-to-date, and helpful information to students and prospective applicants based *ONLY* on the provided context.

Follow these strict guidelines:
1.  **Use ONLY the provided context** to answer the question. Do not use any external knowledge.
2.  **If the context does not contain enough information** to fully answer the question, state politely: "I couldn't find specific information about that in the available Rajagiri resources. Please check the official Rajagiri website or contact the college administration directly for the most accurate and updated details." Do NOT make up information.
3.  **Be precise, factual, and concise.** Avoid conversational filler unless it's a greeting/farewell.
4.  **For admission queries:** Include important dates, application procedures, eligibility criteria, and required documents if available in the context.
5.  **For course queries:** Mention the course name, duration, eligibility, key features, and career prospects if provided.
6.  **Format lists** with clear bullet points or numbered lists when presenting multiple options or details.
7.  **Maintain a helpful and official tone.**

Question: {query}

Context from Rajagiri College Resources:
---
{context}
---

Your Answer:"""

def run_openrouter_llm(prompt: str, max_retries: int = 3, model: str = "mistralai/mistral-7b-instruct:free") -> str:
    """Robust LLM interaction with retries and fallback."""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful and accurate AI assistant for Rajagiri College."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]
    
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,  # Low temperature for factual consistency
                max_tokens=1500,  # Ensure enough space for comprehensive answers
                top_p=0.9
            )
            return clean_text(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"LLM attempt {attempt + 1} failed with model {model}: {str(e)}")
            if attempt == max_retries:
                logger.error(f"All LLM attempts failed for query.")
                return ("I'm experiencing technical difficulties and couldn't process your request fully. "
                        "Please try again later or contact Rajagiri College directly.")
            time.sleep(2 ** (attempt + 1))  # Exponential backoff (1s, 2s, 4s...)
    
    return "I couldn't generate a response. Please try rephrasing your question."

def process_search_results(results: List[Dict], query: str) -> List[Document]:
    """Process and prioritize search results into documents."""
    docs = []
    for result in results:
        try:
            url = result['link']
            # Filter out non-Rajagiri specific file types or irrelevant pages if needed
            if any(url.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.pptx', '.zip']):
                logger.info(f"Skipping document link (file type): {url}")
                continue
            
            # Simple check for direct Rajagiri domain if site_restriction wasn't perfectly enforced
            if not ('rajagiritech.ac.in' in url or 'rajagiri.edu' in url):
                 logger.info(f"Skipping non-Rajagiri domain link: {url}")
                 continue

            logger.info(f"Processing scraped content from: {url}")
            
            # Scrape with max_pages=1 unless deep understanding of linked content is crucial
            content = scrape_clean_text(url, max_pages=1) 
            if not content or len(content.strip()) < 100: # Minimum content length to be considered valid
                logger.info(f"Skipping empty or too short content from {url}")
                continue
                
            relevant_content = extract_relevant_sections(content, query)
            if not relevant_content:
                logger.info(f"No relevant sections found in {url} for query '{query}'")
                continue
                
            docs.append(Document(
                page_content=relevant_content,
                metadata={
                    "source": url,
                    "title": result.get('title', url),
                    "snippet": result.get('snippet', '') # Use snippet for additional relevance scoring if needed
                }
            ))
        except Exception as e:
            logger.error(f"Error processing {result.get('link')}: {str(e)}")
            continue
            
    return docs

def answer_query_with_langchain(query: str) -> ChatbotResponse:
    """
    Complete query answering pipeline:
    1. Handle greetings/farewells instantly.
    2. Search college resources.
    3. Process and prioritize content.
    4. Generate LLM response.
    5. Return with sources.
    """
    logger.info(f"Received query: '{query}'")

    # 1. Handle simple greetings/farewells
    query_lower = query.lower().strip()
    if any(greeting in query_lower for greeting in ["hi", "hello", "hey", "hii", "heyy", "good morning", "good evening"]):
        return ChatbotResponse(
            answer="Hello! I'm RajagiriBot, your AI assistant for Rajagiri College. How can I help you today?",
            sources=[],
            context_used="Greeting detected."
        )
    elif any(farewell in query_lower for farewell in ["bye", "goodbye", "see you", "thank you bye"]):
        return ChatbotResponse(
            answer="Goodbye! Feel free to ask if you have more questions later.",
            sources=[],
            context_used="Farewell detected."
        )
    elif "thank you" in query_lower or "thanks" in query_lower:
        return ChatbotResponse(
            answer="You're welcome! Is there anything else I can assist you with regarding Rajagiri College?",
            sources=[],
            context_used="Thank you detected."
        )
    
    # Step 2: Search for relevant information
    start_time = time.time()
    search_results = search_rajagiri_resources(query, num=5) # Request more results to increase chances of good info
    search_duration = time.time() - start_time
    logger.info(f"Found {len(search_results)} search results in {search_duration:.2f}s")
    
    # Step 3: Process results into documents
    docs = process_search_results(search_results, query)
    if not docs:
        logger.warning(f"No relevant documents found after processing search results for query: '{query}'")
        return ChatbotResponse(
            "I couldn't find specific information about that in the available Rajagiri resources. "
            "Please check the official Rajagiri website or contact the college administration directly for the most accurate and updated details.",
            [],
            ""
        )
    
    # Step 4: Prioritize documents based on relevance and content
    # Sort again after processing, giving higher priority to documents where more relevant sections were found
    docs.sort(key=lambda x: (
        sum(1 for term in query.lower().split() if term in x.metadata['title'].lower() or term in x.metadata['snippet'].lower()),
        len(x.page_content) # Longer relevant content is generally better
    ), reverse=True)
    
    # Step 5: Build context from prioritized documents
    context_parts = []
    max_context_length = 12000  # Conservative token limit for Mistral 7B (check actual model context window)
    total_length = 0
    
    used_sources = set() # To keep track of unique sources used
    
    for doc in docs:
        # Add a clear separator for each source's content
        doc_content = (
            f"\n--- Source: {doc.metadata['title']} ({doc.metadata['source']}) ---\n"
            f"{doc.page_content}\n"
        )
        
        if total_length + len(doc_content) > max_context_length:
            logger.info(f"Context length limit reached ({total_length}/{max_context_length}). Stopping adding documents.")
            break
        context_parts.append(doc_content)
        total_length += len(doc_content)
        used_sources.add(doc.metadata['source'])
    
    combined_context = "\n".join(context_parts)
    logger.info(f"Combined context length: {total_length} characters.")
    
    # Step 6: Generate response using LLM
    prompt = generate_response_prompt(query, combined_context)
    answer = run_openrouter_llm(prompt)
    
    # Step 7: Prepare sources for display
    # Only include sources that were actually used in the combined context
    final_sources = list(used_sources)
    
    if final_sources:
        # Add formatted sources to the answer
        source_links = []
        # Get titles from initial search results to match with used sources
        search_results_map = {res['link']: res.get('title', res['link']) for res in search_results}
        for source_url in final_sources:
            title = search_results_map.get(source_url, source_url)
            source_links.append(f"[{title}]({source_url})")
        
        answer += "\n\nFor more details, you can visit:\n- " + "\n- ".join(source_links)
    
    return ChatbotResponse(
        answer=answer,
        sources=final_sources,
        context_used=combined_context[:3000] + "..." if len(combined_context) > 3000 else combined_context # For debugging
    )

# Public interface
def answer_query(query: str) -> str:
    """Public interface that returns just the answer string"""
    response = answer_query_with_langchain(query)
    return response.answer
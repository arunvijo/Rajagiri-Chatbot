"""Search → Scrape → LLM answer using OpenRouter."""
import os
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

from search_rajagiri_resources import google_search
from scraper import scrape_clean_text

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

# Pick any model available to your OpenRouter account
MODEL_ID = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3-70b-instruct")


def ask_rajagiri_bot(question: str, *, k: int = 6) -> Tuple[str, List[dict]]:
    """Return (answer, source_metadata[])"""
    results = google_search(question, num_results=k)

    # —— Build context ——
    chunks = []
    for res in results:
        body = scrape_clean_text(res["link"])
        if body:
            chunks.append(f"<source>{res['title']} — {res['link']}</source>\n{body}\n")
    context = "\n\n".join(chunks)

    system_msg = (
        "You are an assistant for Rajagiri School of Engineering and Technology, Kochi. "
        "Answer ONLY from the context; if missing say you don't know."
    )

    completion = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
        max_tokens=512,
    )

    answer = completion.choices[0].message.content.strip()
    return answer, results
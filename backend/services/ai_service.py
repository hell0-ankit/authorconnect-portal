import os
import json
import logging
from pathlib import Path
from openai import OpenAI

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FAQ_PATH = BASE_DIR / 'knowledge_base' / 'bookleaf_faq.md'

FAQ_CONTENT = ""
if FAQ_PATH.exists():
    with open(FAQ_PATH, 'r', encoding='utf-8') as f:
        FAQ_CONTENT = f.read()


def analyze_ticket_with_ai(subject: str, description: str) -> dict:
    """
    Analyzes ticket subject and description using OpenAI API.
    Returns suggested category, priority, and draft response based on knowledge base.
    Provides graceful fallback if API is unreachable or key is missing.
    """
    api_key = os.getenv('OPENAI_API_KEY')

    # Fallback default values
    fallback_result = {
        'category': 'ACCOUNT',
        'priority': 'MEDIUM',
        'suggested_response': 'Thank you for contacting BookLeaf Support. We have received your query and our operations team is currently reviewing the details. We will update you shortly.',
    }

    # Rule-based fast classification for fallback
    text_lower = f"{subject} {description}".lower()
    if any(k in text_lower for k in ['royalty', 'payment', 'payout', 'money', 'bank', 'earnings']):
        fallback_result['category'] = 'ROYALTY'
    elif any(k in text_lower for k in ['publish', 'edit', 'cover', 'isbn', 'manuscript', 'proof']):
        fallback_result['category'] = 'PUBLISHING'
    elif any(k in text_lower for k in ['amazon', 'flipkart', 'sales', 'stock', 'delivery', 'order']):
        fallback_result['category'] = 'DISTRIBUTION'
    elif any(k in text_lower for k in ['urgent', 'error', 'bug', 'crash', 'cannot login']):
        fallback_result['priority'] = 'HIGH'

    if not api_key:
        logger.info("OPENAI_API_KEY not configured. Utilizing rule-based fallback classification.")
        return fallback_result

    try:
        client = OpenAI(api_key=api_key)

        system_prompt = f"""
You are the AI Assistant for BookLeaf Publishing Support Portal.
Analyze the author's support ticket and perform three tasks:
1. Classify Category strictly into one of: ROYALTY, PUBLISHING, DISTRIBUTION, ACCOUNT, TECHNICAL.
2. Determine Priority strictly into one of: CRITICAL, HIGH, MEDIUM, LOW.
3. Draft a professional, polite suggested response using the following Knowledge Base:

--- KNOWLEDGE BASE ---
{FAQ_CONTENT}
--- END KNOWLEDGE BASE ---

Return strictly a valid JSON object with keys:
"category", "priority", "suggested_response".
Do not enclose the JSON in markdown code blocks or backticks.
"""

        user_prompt = f"Subject: {subject}\nDescription: {description}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=400,
        )

        content = response.choices[0].message.content.strip()
        data = json.loads(content)

        return {
            'category': data.get('category', fallback_result['category']),
            'priority': data.get('priority', fallback_result['priority']),
            'suggested_response': data.get('suggested_response', fallback_result['suggested_response']),
        }

    except Exception:
        logger.exception("OpenAI ticket analysis failed. Proceeding with fallback.")
        return fallback_result
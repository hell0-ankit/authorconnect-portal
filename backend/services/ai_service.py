
import json
import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FAQ_PATH = BASE_DIR / "knowledge_base" / "bookleaf_faq.md"
FAQ_CONTENT = (
    FAQ_PATH.read_text(encoding="utf-8")
    if FAQ_PATH.exists()
    else ""
)

CATEGORIES = {
    "ROYALTY_PAYMENTS",
    "ISBN_METADATA",
    "PRINTING_QUALITY",
    "DISTRIBUTION",
    "BOOK_STATUS",
    "GENERAL_INQUIRY",
}
PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def _fallback_classification(
    subject: str, description: str
) -> dict[str, str]:
    text = f"{subject} {description}".lower()

    category = "GENERAL_INQUIRY"

    if any(word in text for word in (
        "royalty", "payment", "payout", "bank", "earnings"
    )):
        category = "ROYALTY_PAYMENTS"
    elif any(word in text for word in (
        "isbn", "metadata", "title page", "author name"
    )):
        category = "ISBN_METADATA"
    elif any(word in text for word in (
        "printing", "print quality", "damaged", "pages"
    )):
        category = "PRINTING_QUALITY"
    elif any(word in text for word in (
        "distribution", "amazon", "flipkart",
        "availability", "stock"
    )):
        category = "DISTRIBUTION"
    elif any(word in text for word in (
        "production", "book status", "publishing", "manuscript"
    )):
        category = "BOOK_STATUS"

    priority = "MEDIUM"
    if any(word in text for word in (
        "critical", "urgent", "immediately", "blocked"
    )):
        priority = "HIGH"

    return {
        "category": category,
        "priority": priority,
        "suggested_response": (
            "Thank you for contacting AuthorConnect Support. "
            "Our team will review your query shortly."
        ),
    }


def _generate_json(system_prompt: str, user_prompt: str) -> dict:
    """Generate JSON using the Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=600,
        ),
    )

    content = response.text
    if not content:
        raise ValueError("Gemini returned an empty response.")

    data = json.loads(content)

    if not isinstance(data, dict):
        raise ValueError("Gemini returned an invalid JSON object.")

    return data


def analyze_ticket_with_ai(
    subject: str, description: str
) -> dict[str, str]:
    """Suggest ticket classification without blocking ticket creation."""
    fallback = _fallback_classification(subject, description)

    system_prompt = f"""
Classify this AuthorConnect support ticket.

Choose exactly one category from:
{", ".join(sorted(CATEGORIES))}

Choose exactly one priority from:
{", ".join(sorted(PRIORITIES))}

Return JSON with these string keys:
category, priority, suggested_response.

Keep the suggested response professional and concise.
Do not invent payment dates or claim that actions have been taken.

BookLeaf Knowledge Base:
{FAQ_CONTENT}
"""

    try:
        data = _generate_json(
            system_prompt,
            f"Subject: {subject}\nDescription: {description}",
        )

        category = data.get("category")
        priority = data.get("priority")
        suggested_response = data.get("suggested_response")

        return {
            "category": (
                category
                if category in CATEGORIES
                else fallback["category"]
            ),
            "priority": (
                priority
                if priority in PRIORITIES
                else fallback["priority"]
            ),
            "suggested_response": (
                suggested_response.strip()
                if isinstance(suggested_response, str)
                and suggested_response.strip()
                else fallback["suggested_response"]
            ),
        }

    except Exception as exc:
        logger.warning(
            "Gemini ticket analysis failed; using fallback: %s",
            exc,
        )
        return fallback


def generate_ticket_response_draft(
    subject: str,
    description: str,
    book_context: str,
) -> str | None:
    """Generate an admin-only draft for review; never send it automatically."""

    system_prompt = f"""
You draft a concise, professional support response for an
AuthorConnect administrator to review and edit.

Do not claim that actions have been taken.
Do not invent payment dates, book details, or policy exceptions.
Use the supplied context and knowledge base.
Return JSON with one string key: draft.

Relevant book data:
{book_context or "No book is associated with this ticket."}

BookLeaf Knowledge Base:
{FAQ_CONTENT}
"""

    try:
        data = _generate_json(
            system_prompt,
            f"Subject: {subject}\nAuthor message: {description}",
        )

        draft = data.get("draft")

        if not isinstance(draft, str) or not draft.strip():
            return None

        return draft.strip()[:10000]

    except Exception as exc:
        logger.warning(
            "Gemini admin reply draft generation failed: %s",
            exc,
        )
        return None

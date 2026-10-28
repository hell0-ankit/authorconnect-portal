
import json
import logging
import os
import re
import time
from decimal import Decimal
from pathlib import Path

from google import genai
from google.genai.errors import ServerError
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
MAX_GENERATION_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1
ROYALTY_QUERY_TERMS = (
    "royalt",
    "payout",
    "payment",
    "earnings",
)
ESCALATION_TERMS = (
    "royalty team",
)


def _format_royalty_amount(amount: Decimal | None) -> str | None:
    if amount is None:
        return None
    formatted = format(amount, ",f")
    if "." in formatted:
        formatted = formatted.rstrip("0").rstrip(".")
    return formatted


def _royalty_escalation_response(
    book_title: str | None,
    pending_royalty: Decimal | None,
) -> str:
    if pending_royalty is not None:
        amount = _format_royalty_amount(pending_royalty)
        royalty_detail = f"pending royalty of Rs {amount}"
    else:
        royalty_detail = "pending royalty"
    book_detail = f" for '{book_title}.'" if book_title else "."

    return (
        "Dear Author,\n\n"
        f"Thank you for contacting us regarding your "
        f"{royalty_detail}{book_detail}\n\n"
        "Your request requires review by our royalty team to verify the "
        "pending balance, identify the relevant sales period, and confirm "
        "the payment status. We cannot confirm an exact resolution date "
        "until the details have been reviewed.\n\n"
        "Please note that your request has not yet been confirmed as "
        "escalated. We will provide an update once the review process and "
        "expected timeline are verified.\n\n"
        "Best regards,\n"
        "AuthorConnect Support"
    )


def _royalty_status_response(
    book_title: str | None,
    pending_royalty: Decimal | None,
) -> str:
    if pending_royalty is not None:
        amount = _format_royalty_amount(pending_royalty)
        royalty_detail = f"pending royalty of Rs {amount}"
    else:
        royalty_detail = "pending royalty"
    book_detail = f" for '{book_title}.'" if book_title else "."

    return (
        "Dear Author,\n\n"
        f"Thank you for contacting us regarding your "
        f"{royalty_detail}{book_detail}\n\n"
        "We need to verify the relevant sales period and payment status "
        "before confirming a payment or resolution timeline. We will "
        "provide an update once those details have been reviewed.\n\n"
        "Best regards,\n"
        "AuthorConnect Support"
    )


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


def _generate_text(
    system_prompt: str,
    user_prompt: str,
    response_mime_type: str | None = None,
    max_output_tokens: int = 600,
    thinking_config: types.ThinkingConfig | None = None,
) -> str:
    """Generate text using the Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)
    config = {
        "system_instruction": system_prompt,
        "temperature": 0.2,
        "max_output_tokens": max_output_tokens,
    }
    if response_mime_type:
        config["response_mime_type"] = response_mime_type
    if thinking_config:
        config["thinking_config"] = thinking_config

    for attempt in range(MAX_GENERATION_ATTEMPTS):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(**config),
            )
            break
        except ServerError as exc:
            if exc.code != 503 or attempt == MAX_GENERATION_ATTEMPTS - 1:
                raise
            delay = RETRY_DELAY_SECONDS * (2 ** attempt)
            logger.warning(
                "Gemini returned 503; retrying generation in %s seconds.",
                delay,
            )
            time.sleep(delay)

    content = response.text
    if not content:
        raise ValueError("Gemini returned an empty response.")

    return content


def _generate_json(system_prompt: str, user_prompt: str) -> dict:
    """Generate JSON using the Gemini API."""
    content = _generate_text(
        system_prompt,
        user_prompt,
        response_mime_type="application/json",
    )
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
    *,
    book_title: str | None = None,
    pending_royalty: Decimal | None = None,
    conversation_context: str = "",
) -> str | None:
    """Generate an admin-only draft for review; never send it automatically."""
    conversation = "\n".join(
        part
        for part in (subject, description, conversation_context)
        if part
    )
    normalized_conversation = conversation.lower()
    is_royalty_query = any(
        term in normalized_conversation for term in ROYALTY_QUERY_TERMS
    )

    if is_royalty_query:
        is_escalation_request = any(
            term in normalized_conversation for term in ESCALATION_TERMS
        ) or re.search(
            r"\b(?:escalat\w*|forward\w*|refer\w*)\b",
            normalized_conversation,
        )
        if is_escalation_request:
            return _royalty_escalation_response(
                book_title,
                pending_royalty,
            )
        return _royalty_status_response(
            book_title,
            pending_royalty,
        )

    system_prompt = f"""
You draft a concise, professional support response for an
AuthorConnect administrator to review and edit.

Do not claim that actions have been taken.
Do not invent payment dates, book details, or policy exceptions.
Never provide a payment or resolution date unless it is verified in the
supplied records or explicitly stated in the configured business policy.
Do not treat a pending balance as evidence of its sales month or payment
status. Never say a request was escalated, created, or assigned unless the
corresponding action successfully completed and that result is supplied.
Use the supplied context and knowledge base.
Keep the draft to one short paragraph, ideally under 100 words.
Return only the reply draft as plain text. Do not wrap it in JSON or quotes.

Relevant book data:
{book_context or "No book is associated with this ticket."}

Configured business policy and knowledge base (do not substitute other
payment schedules):
{FAQ_CONTENT or "No verified business policy is configured. Do not provide payment schedules or specific dates."}
"""

    try:
        draft = _generate_text(
            system_prompt,
            f"Subject: {subject}\nAuthor message: {description}",
            max_output_tokens=220,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.MINIMAL,
            ),
        )

        if not draft.strip():
            return None

        return draft.strip()[:10000]

    except Exception as exc:
        logger.warning(
            "Gemini admin reply draft generation failed: %s",
            exc,
        )
        return None

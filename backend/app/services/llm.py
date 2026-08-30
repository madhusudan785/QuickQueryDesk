"""LLM-powered ticket classification service using Google Gemini.

This module provides AI classification of support tickets into categories
and priority levels using the Gemini API via httpx.
"""

import json
import logging
from typing import TypedDict

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Valid classification values
VALID_CATEGORIES = {"IT", "HR", "Finance", "Admin", "Other"}
VALID_PRIORITIES = {"Low", "Medium", "High"}

# Default fallback values when the LLM fails or returns invalid data
DEFAULT_CATEGORY = "Other"
DEFAULT_PRIORITY = "Medium"

CLASSIFICATION_PROMPT = """You are an expert IT Helpdesk AI assistant. Your task is to classify support tickets.

Given a support ticket with a title and description, you must determine:

1. **Category** — exactly one of: IT, HR, Finance, Admin, Other
   - IT: Software issues, hardware problems, VPN, email, network, password resets, system access, laptops, printers
   - HR: Leave requests, payroll questions, benefits, onboarding, policies, workplace issues, training
   - Finance: Expense reimbursements, invoices, budget questions, purchase orders, corporate cards
   - Admin: Office supplies, facilities, meeting rooms, building access, parking, general admin requests
   - Other: Anything that doesn't clearly fit the above categories

2. **Priority** — exactly one of: Low, Medium, High
   - High: System outages, security incidents, cannot work at all, blocking multiple people, urgent deadlines
   - Medium: Partial functionality loss, important but workarounds exist, affects one person
   - Low: General questions, nice-to-have requests, informational queries, non-urgent improvements

Classify this ticket:

Title: {title}
Description: {description}

Respond with ONLY a valid JSON object in this exact format, nothing else:
{{"category": "<one of: IT, HR, Finance, Admin, Other>", "priority": "<one of: Low, Medium, High>"}}"""


class ClassificationResult(TypedDict):
    """Result of ticket classification."""
    category: str
    priority: str


def _parse_classification(raw_response: str) -> ClassificationResult:
    """Parse and validate the LLM's JSON response.
    
    Falls back to defaults if the response is invalid.
    """
    try:
        # Strip markdown code fences if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()

        data = json.loads(cleaned)

        category = data.get("category", DEFAULT_CATEGORY)
        priority = data.get("priority", DEFAULT_PRIORITY)

        # Validate against allowed values
        if category not in VALID_CATEGORIES:
            logger.warning(f"LLM returned invalid category: {category}, using default")
            category = DEFAULT_CATEGORY
        if priority not in VALID_PRIORITIES:
            logger.warning(f"LLM returned invalid priority: {priority}, using default")
            priority = DEFAULT_PRIORITY

        return ClassificationResult(category=category, priority=priority)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse LLM classification response: {e}. Raw: {raw_response}")
        return ClassificationResult(category=DEFAULT_CATEGORY, priority=DEFAULT_PRIORITY)


async def classify_ticket(title: str, description: str) -> ClassificationResult:
    """Classify a support ticket using the Gemini LLM.
    
    Args:
        title: The ticket title/subject.
        description: The detailed ticket description.
        
    Returns:
        ClassificationResult with category and priority.
        Falls back to defaults if LLM call fails.
    """
    settings = get_settings()

    # If no API key is configured, return defaults immediately
    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your-gemini-api-key-here":
        logger.warning("No LLM API key configured. Using default classification.")
        return ClassificationResult(category=DEFAULT_CATEGORY, priority=DEFAULT_PRIORITY)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.LLM_API_KEY}"
        prompt = CLASSIFICATION_PROMPT.format(title=title, description=description)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1024,
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "category": {
                            "type": "STRING",
                            "enum": ["IT", "HR", "Finance", "Admin", "Other"],
                        },
                        "priority": {
                            "type": "STRING",
                            "enum": ["Low", "Medium", "High"],
                        },
                    },
                    "required": ["category", "priority"],
                },
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        logger.info(f"LLM classification raw response: {raw_text}")
        result = _parse_classification(raw_text)
        logger.info(f"Ticket classified - Category: {result['category']}, Priority: {result['priority']}")

        return result

    except Exception as e:
        logger.error(f"LLM classification failed: {e}")
        return ClassificationResult(category=DEFAULT_CATEGORY, priority=DEFAULT_PRIORITY)


DRAFT_REPLY_PROMPT = """You are a professional IT Helpdesk support agent. Generate a helpful, empathetic reply to resolve the following support ticket.

{context_section}

Ticket Details:
- Title: {title}
- Description: {description}
- Category: {category}
- Priority: {priority}

Instructions:
1. Address the employee professionally and empathetically.
2. If knowledge base articles were provided above, use them to give specific, actionable steps.
3. Provide clear, numbered steps the employee can follow.
4. If the issue requires further investigation or escalation, mention that clearly.
5. Keep the tone professional but friendly.
6. Do NOT include a subject line or salutation with "Dear" — just start with a greeting like "Hi" or "Hello".
7. End with an offer to help further.

Write the reply now:"""


async def generate_draft_reply(
    title: str,
    description: str,
    category: str,
    priority: str,
) -> str:
    """Generate an AI draft reply using RAG context from the knowledge base.

    Args:
        title: The ticket title.
        description: The ticket description.
        category: The classified category.
        priority: The classified priority.

    Returns:
        A draft reply string, or empty string if generation fails.
    """
    from app.rag.engine import retrieve_context_for_reply

    settings = get_settings()

    if not settings.LLM_API_KEY or settings.LLM_API_KEY == "your-gemini-api-key-here":
        logger.warning("No LLM API key configured. Skipping draft reply generation.")
        return ""

    try:
        # Retrieve relevant KB context via RAG
        query = f"{title} {description}"
        rag_context = await retrieve_context_for_reply(query, top_k=3)

        if rag_context:
            context_section = f"""Relevant Knowledge Base Articles (use these to inform your response):

{rag_context}

---"""
        else:
            context_section = "(No relevant knowledge base articles found. Provide general guidance.)"

        prompt = DRAFT_REPLY_PROMPT.format(
            context_section=context_section,
            title=title,
            description=description,
            category=category,
            priority=priority,
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.LLM_MODEL}:generateContent?key={settings.LLM_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1024,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        draft = data["candidates"][0]["content"]["parts"][0]["text"].strip()

        logger.info(f"AI draft reply generated ({len(draft)} chars)")
        return draft

    except Exception as e:
        logger.error(f"Draft reply generation failed: {e}")
        return ""


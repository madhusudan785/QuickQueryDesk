"""LLM-powered ticket classification service using Groq or Google Gemini.

This module provides AI classification of support tickets into categories
and priority levels using Groq or Gemini APIs directly, with reliable single-attempt
execution and graceful fallback draft generation.
"""

import asyncio
import json
import logging
import re
from typing import TypedDict

USE_GROQ_SDK = False
USE_GENAI_SDK = False
USE_OLD_GENAI = False

try:
    from groq import Groq
    USE_GROQ_SDK = True
except Exception:
    pass

try:
    from google import genai
    from google.genai import types
    USE_GENAI_SDK = True
except Exception:
    try:
        import google.generativeai as old_genai
        USE_OLD_GENAI = True
    except Exception:
        pass

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
    is_fallback: bool
    status: str


def _sanitize_log_message(msg: str) -> str:
    """Sanitize any potential keys, tokens, or credentials from log strings."""
    sanitized = re.sub(r'(api_?key|token|password|secret)=[^&\s"\']+', r'\1=[REDACTED]', str(msg), flags=re.IGNORECASE)
    return sanitized


def _parse_classification(raw_response: str) -> ClassificationResult:
    """Parse and validate the LLM's JSON response."""
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

        is_fallback = False
        # Validate against allowed values
        if category not in VALID_CATEGORIES:
            logger.warning(f"LLM returned invalid category: {category}, using fallback default")
            category = DEFAULT_CATEGORY
            is_fallback = True
        if priority not in VALID_PRIORITIES:
            logger.warning(f"LLM returned invalid priority: {priority}, using fallback default")
            priority = DEFAULT_PRIORITY
            is_fallback = True

        status = "CLASSIFICATION_FAILED" if is_fallback else "CLASSIFIED"
        return ClassificationResult(category=category, priority=priority, is_fallback=is_fallback, status=status)

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Failed to parse LLM classification response: {e}. Raw: {_sanitize_log_message(raw_response)}")
        return ClassificationResult(
            category=DEFAULT_CATEGORY,
            priority=DEFAULT_PRIORITY,
            is_fallback=True,
            status="CLASSIFICATION_FAILED",
        )


def _sync_call_llm_classification(settings, prompt: str) -> str:
    """Synchronous function to perform classification via Groq or Gemini SDK."""
    if USE_GROQ_SDK and settings.LLM_API_KEY.startswith("gsk_"):
        client = Groq(api_key=settings.LLM_API_KEY)
        completion = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert IT Helpdesk AI assistant. Respond ONLY with a JSON object containing category and priority."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        return completion.choices[0].message.content.strip()
    elif USE_GENAI_SDK:
        client = genai.Client(api_key=settings.LLM_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema={
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
            ),
        )
        return response.text
    elif USE_OLD_GENAI:
        old_genai.configure(api_key=settings.LLM_API_KEY)
        response_schema = {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["IT", "HR", "Finance", "Admin", "Other"],
                },
                "priority": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                },
            },
            "required": ["category", "priority"],
        }
        model = old_genai.GenerativeModel(
            model_name=settings.LLM_MODEL,
            generation_config=old_genai.GenerationConfig(
                temperature=0.2,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        response = model.generate_content(prompt)
        return response.text
    else:
        raise RuntimeError("No LLM SDK (Groq or Gemini) available.")


async def classify_ticket(title: str, description: str) -> ClassificationResult:
    """Classify a support ticket using Groq/Gemini LLM with single-attempt execution.

    Args:
        title: The ticket title/subject.
        description: The detailed ticket description.

    Returns:
        ClassificationResult with category, priority, is_fallback, and status.
    """
    settings = get_settings()

    if not settings.LLM_API_KEY or settings.LLM_API_KEY in ("your-gemini-api-key-here", "your-groq-api-key-here"):
        logger.warning("No LLM API key configured. Using fallback classification.")
        return ClassificationResult(
            category=DEFAULT_CATEGORY,
            priority=DEFAULT_PRIORITY,
            is_fallback=True,
            status="CLASSIFICATION_FAILED",
        )

    try:
        prompt = CLASSIFICATION_PROMPT.format(title=title, description=description)

        raw_text = await asyncio.to_thread(
            _sync_call_llm_classification,
            settings,
            prompt,
        )

        logger.info("LLM classification response received.")
        result = _parse_classification(raw_text)
        if not result["is_fallback"]:
            logger.info(f"Ticket classified - Category: {result['category']}, Priority: {result['priority']}")
        return result

    except Exception as e:
        safe_err = _sanitize_log_message(str(e))
        logger.error(f"LLM classification failed: {safe_err}")
        return ClassificationResult(
            category=DEFAULT_CATEGORY,
            priority=DEFAULT_PRIORITY,
            is_fallback=True,
            status="CLASSIFICATION_FAILED",
        )


DRAFT_REPLY_PROMPT = """You are a direct, efficient IT Support assistant. Generate a concise, straightforward reply to resolve the following support ticket.

{context_section}

Ticket Details:
- Title: {title}
- Description: {description}
- Category: {category}
- Priority: {priority}

Instructions:
1. Be direct, concise, and straight to the point.
2. Skip verbose greetings, empathy filler, or repetitive closing fluff (do NOT include "I understand how frustrating...", "Thank you for reaching out...", "Best regards, IT Support").
3. Start directly with a simple "Hi," followed immediately by clear, actionable troubleshooting steps.
4. Format steps as short, clean numbered items.
5. Write links as plain text URLs (e.g. https://itportal.company.com/vpn). Do NOT output redundant markdown links like [URL](URL) or heavy bracket formatting.
6. Include relevant search keywords (e.g., specific error messages, app names, portal addresses, system setting paths) so the employee can easily search for more details independently.
7. Keep the response brief to save output tokens.

Write the concise reply now:"""


def _clean_draft_reply(text: str) -> str:
    """Clean unwanted markdown artifacts and redundant link tags from the draft reply."""
    if not text:
        return ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(
            line for line in lines
            if not line.strip().startswith("```")
        ).strip()

    # Fix redundant markdown links like [https://url](https://url) -> https://url
    cleaned = re.sub(r'\[(https?://[^\s\]]+)\]\(\1\)', r'\1', cleaned)
    # Fix markdown links [Label](URL) -> Label (URL) to avoid raw markdown bracket artifacts
    cleaned = re.sub(r'\[([^\]]+)\]\((https?://[^\s\)]+)\)', r'\1 (\2)', cleaned)

    return cleaned.strip()


def _create_fallback_draft(title: str, description: str, rag_context: str) -> str:
    """Generate a clear, professional fallback draft when LLM fails or is unconfigured."""
    if rag_context:
        return (
            "Hi,\n\n"
            "Thank you for reaching out to IT Support. Based on our Knowledge Base, "
            "here is the guidance for your request:\n\n"
            f"{rag_context}\n\n"
            "If the issue persists, an IT support agent will review your ticket and follow up shortly."
        )
    else:
        return (
            "Hi,\n\n"
            f'Thank you for submitting your support ticket regarding "{title}". '
            "Our support team has received your request and an agent will review it shortly.\n\n"
            "In the meantime, please ensure you have saved any work and restarted the "
            "affected application or device if applicable."
        )


def _sync_call_llm_draft(settings, prompt: str) -> str:
    """Synchronous function to generate draft reply via Groq or Gemini SDK."""
    if USE_GROQ_SDK and settings.LLM_API_KEY.startswith("gsk_"):
        client = Groq(api_key=settings.LLM_API_KEY)
        completion = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a direct, efficient IT Support assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return completion.choices[0].message.content.strip() if completion.choices[0].message.content else ""
    elif USE_GENAI_SDK:
        client = genai.Client(api_key=settings.LLM_API_KEY)
        response = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1024,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text.strip() if response.text else ""
    elif USE_OLD_GENAI:
        old_genai.configure(api_key=settings.LLM_API_KEY)
        model = old_genai.GenerativeModel(
            model_name=settings.LLM_MODEL,
            generation_config=old_genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1024,
            ),
        )
        response = model.generate_content(prompt)
        return response.text.strip() if response.text else ""
    else:
        raise RuntimeError("No LLM SDK available.")


async def generate_draft_reply_ext(
    title: str,
    description: str,
    category: str,
    priority: str,
) -> tuple[str, str]:
    """Generate an AI draft reply using RAG context with graceful fallback handling.

    Returns:
        tuple[draft_reply_string, pipeline_status]
        where pipeline_status is "COMPLETED" (or "COMPLETED_FALLBACK").
    """
    from app.rag.engine import retrieve_context_for_reply

    settings = get_settings()
    query = f"{title} {description}"
    rag_context = await retrieve_context_for_reply(query, top_k=3)

    if not settings.LLM_API_KEY or settings.LLM_API_KEY in ("your-gemini-api-key-here", "your-groq-api-key-here"):
        logger.warning("No valid LLM API key configured. Generating fallback draft response.")
        fallback = _create_fallback_draft(title, description, rag_context)
        return fallback, "COMPLETED_FALLBACK"

    try:
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

        raw_draft = await asyncio.to_thread(
            _sync_call_llm_draft,
            settings,
            prompt,
        )

        draft = _clean_draft_reply(raw_draft)
        if draft:
            logger.info(f"AI draft reply generated successfully via LLM ({len(draft)} chars).")
            return draft, "COMPLETED"
        else:
            logger.warning("LLM returned empty text. Generating fallback draft response.")
            fallback = _create_fallback_draft(title, description, rag_context)
            return fallback, "COMPLETED_FALLBACK"

    except Exception as e:
        safe_err = _sanitize_log_message(str(e))
        logger.error(f"LLM draft reply generation failed: {safe_err}. Generating fallback draft response.")
        fallback = _create_fallback_draft(title, description, rag_context)
        return fallback, "COMPLETED_FALLBACK"


async def generate_draft_reply(
    title: str,
    description: str,
    category: str,
    priority: str,
) -> str:
    """Convenience wrapper for generate_draft_reply_ext returning only the draft string."""
    draft, _ = await generate_draft_reply_ext(title, description, category, priority)
    return draft




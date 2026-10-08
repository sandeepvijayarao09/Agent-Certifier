"""A reasonably well-behaved agent, used as the 'good' sample for Agent Certifier."""
import asyncio
import logging
import os
import re
from functools import lru_cache
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

API_KEY = os.getenv("LLM_API_KEY")
LLM_URL = os.getenv("LLM_URL", "https://llm.example.com/v1/complete")
MAX_INPUT_CHARS = 2000
REQUEST_TIMEOUT_S = 10.0

BLOCKED_TOPICS = ("self-harm", "weapons")


def sanitize(text: str) -> str:
    """Strip control characters and cap the length of untrusted input."""
    text = re.sub(r"[\x00-\x1f]", "", text)
    return text[:MAX_INPUT_CHARS].strip()


def redact_pii(text: str) -> str:
    """Mask email addresses and phone numbers before logging (GDPR data minimization)."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "[email]", text)
    return re.sub(r"\+?\d[\d\s-]{7,}\d", "[phone]", text)


@lru_cache(maxsize=256)
def system_prompt() -> str:
    """Return the fixed system prompt. User text is never concatenated into it."""
    return "You are a support assistant. Refuse requests outside customer support."


async def ask_model(client: httpx.AsyncClient, user_text: str) -> Optional[str]:
    """Call the model with a timeout and return its text, or None on failure."""
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt()},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 512,
    }
    try:
        resp = await client.post(
            LLM_URL,
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        return resp.json().get("text")
    except httpx.HTTPError as exc:
        logger.warning("model call failed: %s", exc)
        return None


def needs_human_review(reply: str) -> bool:
    """Escalate to a human when the reply touches a blocked topic."""
    return any(topic in reply.lower() for topic in BLOCKED_TOPICS)


async def handle(user_input: str) -> str:
    """Validate input, ask the model, and apply output filtering with human oversight."""
    if not isinstance(user_input, str) or not user_input.strip():
        raise ValueError("input must be a non-empty string")
    clean = sanitize(user_input)
    logger.info("request: %s", redact_pii(clean))
    async with httpx.AsyncClient() as client:
        reply = await ask_model(client, clean)
    if reply is None:
        return "Sorry, I can't answer right now. Please try again later."
    if needs_human_review(reply):
        logger.info("escalated to human review")
        return "I've passed this to a human teammate who will follow up."
    return reply


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(handle("Where is my order?")))

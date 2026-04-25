import logging
import time
from typing import Iterable

from groq import Groq

from config.settings import (
    GROQ_API_KEY,
    LLM_MAX_RETRIES,
    LLM_TIMEOUT_SECONDS,
    MODEL_NAME,
)


logger = logging.getLogger(__name__)
if not GROQ_API_KEY:
    raise ValueError("Set GROQ_API_KEY in your environment or .env file before running LLM features.")

client = Groq(api_key=GROQ_API_KEY, timeout=LLM_TIMEOUT_SECONDS)


def complete_chat(
    messages: Iterable[dict],
    *,
    fallback: str | None = None,
    model: str = MODEL_NAME,
    max_retries: int = LLM_MAX_RETRIES,
    temperature: float = 0.2,
) -> str:
    """
    Call the configured Groq chat model with basic retry/fallback behavior.

    The UI should not crash because of a transient LLM/API issue. If all retries
    fail and a fallback is provided, the fallback is returned. Otherwise a
    RuntimeError is raised with the original exception chained.
    """
    message_list = list(messages)
    attempts = max(1, max_retries + 1)
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=message_list,
                temperature=temperature,
                timeout=LLM_TIMEOUT_SECONDS,
            )
            content = response.choices[0].message.content
            if content and content.strip():
                return content.strip()
            raise ValueError("LLM response was empty.")
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Groq chat completion failed on attempt %s/%s: %s",
                attempt + 1,
                attempts,
                exc,
            )
            if attempt < attempts - 1:
                time.sleep(0.75 * (attempt + 1))

    if fallback is not None:
        return fallback

    raise RuntimeError("Groq chat completion failed after retries.") from last_error

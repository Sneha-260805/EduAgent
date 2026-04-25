import json
import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from agents.llm_client import complete_chat


class EvaluationResult(BaseModel):
    understanding_level: Literal["good", "partial", "poor"] = "partial"
    weak_concepts: list[str] = Field(default_factory=list)
    feedback: str = ""
    recommended_action: Literal[
        "advance",
        "re-explain",
        "give easier example",
        "give more practice",
    ] = "give more practice"


def _extract_json_object(raw: str) -> dict:
    """
    Extract and parse the first JSON object from an LLM response.
    Handles accidental markdown fences or short surrounding text.
    """
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"```$", "", raw).strip()

    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _validate_evaluation(data: dict) -> dict:
    try:
        result = EvaluationResult.model_validate(data)
    except AttributeError:
        result = EvaluationResult.parse_obj(data)
    return result.model_dump() if hasattr(result, "model_dump") else result.dict()


def generate_followup_question(user_question: str, tutor_answer: str, level: str, topic: str) -> str:
    """
    Generate one short conceptual follow-up question to test learner understanding.
    """
    prompt = f"""
You are an evaluator for an adaptive AI tutor.

Topic: {topic}
Learner level: {level}

Original learner question:
{user_question}

Tutor's answer:
{tutor_answer}

Generate ONE short follow-up question to test whether the learner understood the main idea.

Rules:
- Match the learner's level.
- Focus on conceptual understanding, not memorization.
- Keep it short and clear.
- Return only the question.
"""

    fallback_question = (
        "In your own words, what is the main idea from the explanation?"
    )

    return complete_chat(
        [{"role": "user", "content": prompt}],
        fallback=fallback_question,
        temperature=0.2,
    )


def evaluate_followup_response(
    topic: str,
    level: str,
    followup_question: str,
    learner_reply: str
) -> dict:
    """
    Evaluate the learner's reply to the follow-up question.

    Returns:
    {
        "understanding_level": "good" | "partial" | "poor",
        "weak_concepts": [ ... ],
        "feedback": "...",
        "recommended_action": "advance" | "re-explain" | "give easier example" | "give more practice"
    }
    """
    prompt = f"""
You are an evaluator for an adaptive AI tutor.

Topic: {topic}
Learner level: {level}

Follow-up question:
{followup_question}

Learner reply:
{learner_reply}

Evaluate the learner's reply.

Return valid JSON only with exactly these keys:
- understanding_level: one of ["good", "partial", "poor"]
- weak_concepts: list of short concept names
- feedback: short educational feedback
- recommended_action: one of ["advance", "re-explain", "give easier example", "give more practice"]

Rules:
- Be fair and educational.
- If the learner is partly correct, mark as "partial".
- Keep weak_concepts short and specific.
- Do not include markdown.
- Return valid JSON only.
"""

    raw = complete_chat(
        [{"role": "user", "content": prompt}],
        fallback="",
        temperature=0.0,
    )

    try:
        result = _validate_evaluation(_extract_json_object(raw))
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError):
        # Safe fallback if the LLM/API returns invalid or non-JSON content.
        result = {
            "understanding_level": "partial",
            "weak_concepts": [],
            "feedback": "Could not reliably parse the learner evaluation. Review the learner response manually.",
            "recommended_action": "give more practice"
        }

    return result

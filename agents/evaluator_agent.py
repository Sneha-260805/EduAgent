import json
from groq import Groq
from config.settings import GROQ_API_KEY, MODEL_NAME

client = Groq(api_key=GROQ_API_KEY)


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

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


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

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
    except Exception:
        # Safe fallback if LLM returns non-JSON
        result = {
            "understanding_level": "partial",
            "weak_concepts": [],
            "feedback": "Could not reliably parse the learner evaluation. Review the learner response manually.",
            "recommended_action": "give more practice"
        }

    # Extra safety
    result.setdefault("understanding_level", "partial")
    result.setdefault("weak_concepts", [])
    result.setdefault("feedback", "")
    result.setdefault("recommended_action", "give more practice")

    return result
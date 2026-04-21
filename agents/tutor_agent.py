from groq import Groq

from config.settings import GROQ_API_KEY, MODEL_NAME
from ml.classifier import predict_level
from ml.topic_detector import detect_best_topic
from ml.retriever import retrieve_examples, df
from agents.memory_agent import build_memory_hint

client = Groq(api_key=GROQ_API_KEY)


def format_examples(examples_df):
    """
    Convert retrieved examples DataFrame into prompt text.
    """
    if examples_df is None or len(examples_df) == 0:
        return "No examples found."

    parts = []
    for i, row in enumerate(examples_df.itertuples(index=False), 1):
        parts.append(
            f"Example {i}:\n"
            f"Question: {row.question}\n"
            f"Answer: {row.answer}\n"
            f"Topic: {row.topic}"
        )
    return "\n\n".join(parts)


def generate_tutor_response(user_question: str, profile: dict):
    """
    Main Tutor Agent function.

    Steps:
    1. Predict learner difficulty level
    2. Detect topic
    3. Retrieve examples from dataset
    4. Build memory hint from learner profile
    5. Build tutor prompt
    6. Generate adaptive answer from Groq LLM

    Returns:
        level, confidence, topic, examples_df, answer
    """
    level, confidence = predict_level(user_question)
    topic = detect_best_topic(user_question, level, df)
    examples = retrieve_examples(user_question, level, top_n=2)

    examples_text = format_examples(examples)
    memory_hint = build_memory_hint(profile, topic)

    prompt = f"""
You are EduAgent, an adaptive AI tutor.

Student question:
{user_question}

Detected student level:
{level}

Detected topic:
{topic}

Learner memory hint:
{memory_hint}

Reference examples for style guidance only:
{examples_text}

Instructions:
- Answer according to the detected level.
- For beginner: use simple words, intuition, and easy examples.
- For intermediate: explain clearly with moderate detail and 1-2 key technical terms.
- For advanced: give a deeper, more technical explanation.
- Do not copy the examples directly.
- Use the examples only to match explanation style and difficulty.
- Use the learner memory hint to avoid repeating the same explanation style.
- If weak areas are listed, address them explicitly.
- If the learner has already seen this topic, do not restart with the exact same beginner introduction.
- Keep the answer educational, structured, and concise.

Now answer the student's question.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content.strip()
    return level, confidence, topic, examples, answer
from ml.classifier import predict_level
from ml.topic_detector import detect_best_topic
from ml.retriever import retrieve_examples, df as RETRIEVER_DF
from agents.memory_agent import build_memory_hint, build_evaluation_strategy_hint
from agents.llm_client import complete_chat


def format_examples(examples_df):
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


def infer_teaching_mode(evaluation_strategy_hint: str) -> str:
    """
    Extract a simple teaching mode from the evaluator strategy hint.
    """
    hint_lower = evaluation_strategy_hint.lower()

    if "teaching mode: remedial" in hint_lower:
        return "remedial"
    elif "teaching mode: clarification" in hint_lower:
        return "clarification"
    elif "teaching mode: advance" in hint_lower:
        return "advance"
    return "default"


def build_mode_specific_instruction(teaching_mode: str) -> str:
    """
    Return strong tutor instructions based on teaching mode.
    """
    if teaching_mode == "remedial":
        return """
Mode-specific instructions:
- Re-teach from scratch.
- Use very simple wording.
- Use one small concrete example.
- Explain in 4 to 6 short sentences.
- Focus on one main idea first before adding detail.
- Avoid abstract definitions unless absolutely necessary.
- Avoid repeating the same explanation style or analogy used earlier for this topic.
- Start with: "Let's simplify it completely."
"""
    elif teaching_mode == "clarification":
        return """
Mode-specific instructions:
- Briefly restate the main idea in one or two simple sentences.
- Then focus on the weak or confusing concept.
- Use one clear example.
- Do not repeat the whole long explanation.
- Keep the answer focused and moderately short.
"""
    elif teaching_mode == "advance":
        return """
Mode-specific instructions:
- Assume the learner understood the basics.
- Avoid repeating the full beginner introduction.
- Give a slightly deeper explanation.
- Connect the concept to a related next-step idea.
- Keep the answer clear but more intellectually rich.
"""
    else:
        return """
Mode-specific instructions:
- Give a normal level-appropriate explanation.
"""


def generate_tutor_response(user_question: str, profile: dict):
    level, confidence = predict_level(user_question)
    topic = detect_best_topic(user_question, level, RETRIEVER_DF)
    if not topic:
        topic = "general"
    examples = retrieve_examples(user_question, level, top_n=2)

    examples_text = format_examples(examples)
    memory_hint = build_memory_hint(profile, topic)
    evaluation_strategy_hint = build_evaluation_strategy_hint(profile, topic)
    teaching_mode = infer_teaching_mode(evaluation_strategy_hint)
    mode_instruction = build_mode_specific_instruction(teaching_mode)

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

Recent evaluator strategy hint:
{evaluation_strategy_hint if evaluation_strategy_hint else "No recent evaluation strategy available for this topic."}

Retrieved dataset examples:
{examples_text}

General instructions:
- Answer according to the detected level.
- For beginner: use simple words, intuition, and easy examples.
- For intermediate: explain clearly with moderate detail and 1-2 key technical terms.
- For advanced: give a deeper, more technical explanation.
- Treat retrieved examples as supporting context, not as guaranteed ground truth.
- Use relevant examples to ground the explanation style and topic coverage.
- Do not copy the retrieved examples directly.
- Use learner memory to avoid repeating the same explanation style.
- If weak areas are listed, address them explicitly.
- If recent evaluator strategy exists, adapt the answer accordingly.
- Keep the answer educational, structured, and concise.

{mode_instruction}

Now answer the student's question.
"""

    fallback_answer = (
        "I could not reach the tutor model reliably right now. "
        "Please try asking again in a moment. Your question was still classified "
        f"as {level} and mapped to the topic {topic}."
    )

    answer = complete_chat(
        [{"role": "user", "content": prompt}],
        fallback=fallback_answer,
        temperature=0.25,
    )
    return level, confidence, topic, examples, answer

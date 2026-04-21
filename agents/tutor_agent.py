from groq import Groq
from config.settings import GROQ_API_KEY, MODEL_NAME
from ml.classifier import predict_level
from ml.retriever import retrieve_examples
from ml.topic_detector import detect_best_topic
from ml.retriever import df
from ml.prompts import build_tutor_prompt


client = Groq(api_key=GROQ_API_KEY)


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


def examples_to_markdown(examples_df):
    if examples_df is None or len(examples_df) == 0:
        return "No examples retrieved."
    lines = []
    for i, row in enumerate(examples_df.itertuples(index=False), 1):
        lines.append(
            f"### Example {i}\n"
            f"**Question:** {row.question}\n\n"
            f"**Answer:** {row.answer}\n\n"
            f"**Level:** {row.level}\n\n"
            f"**Topic:** {row.topic}"
        )
    return "\n---\n".join(lines)


def generate_tutor_response(user_question, memory_hint="No prior topic memory."):
    level, confidence = predict_level(user_question)
    topic = detect_best_topic(user_question, level, df)
    examples = retrieve_examples(user_question, level, top_n=2)
    examples_text = format_examples(examples)

    prompt = build_tutor_prompt(user_question, level, topic, examples_text, memory_hint)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content
    return level, confidence, topic, examples, answer

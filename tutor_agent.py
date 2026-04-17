from groq import Groq
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
import torch.nn.functional as F
from example_retriever import retrieve_examples, detect_best_topic
import os

# -----------------------------
# CONFIG
# -----------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Set GROQ_API_KEY in your environment before running this script.")

client = Groq(api_key=GROQ_API_KEY)

tokenizer = DistilBertTokenizer.from_pretrained("./difficulty_classifier")
model = DistilBertForSequenceClassification.from_pretrained("./difficulty_classifier")
model.eval()

labels = ["beginner", "intermediate", "advanced"]

# -----------------------------
# CLASSIFIER
# -----------------------------
def predict_level(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = F.softmax(logits, dim=1)
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]
    predicted_label = labels[pred_idx]

    if max(confidence) < 0.6:
        predicted_label = "intermediate"

    return predicted_label, confidence

# -----------------------------
# FORMAT EXAMPLES
# -----------------------------
def format_examples(examples_df):
    parts = []
    for i, row in enumerate(examples_df.itertuples(index=False), 1):
        parts.append(
            f"Example {i}:\n"
            f"Question: {row.question}\n"
            f"Answer: {row.answer}\n"
            f"Topic: {row.topic}"
        )
    return "\n\n".join(parts)

# -----------------------------
# GENERATE TUTOR RESPONSE
# -----------------------------
def generate_tutor_response(user_question):
    level, confidence = predict_level(user_question)
    topic = detect_best_topic(user_question, level)
    examples = retrieve_examples(user_question, level, top_n=2)
    examples_text = format_examples(examples)

    prompt = f"""
You are EduAgent, an adaptive AI tutor.

Student question:
{user_question}

Detected student level:
{level}

Detected topic:
{topic}

Reference examples for style guidance only:
{examples_text}

Instructions:
- Answer according to the detected level.
- For beginner: use simple words, intuition, and easy examples.
- For intermediate: explain clearly with moderate detail and 1-2 key technical terms.
- For advanced: give a deeper, more technical explanation.
- Do not copy the examples directly.
- Use the examples only to match explanation style and difficulty.
- If the student's question is short and basic, prefer slightly simpler wording.
- Keep the answer educational, structured, and concise.

Now answer the student's question.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content
    return level, confidence, topic, examples, answer

# -----------------------------
# MAIN LOOP
# -----------------------------
if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or quit): ").strip()
        if q.lower() == "quit":
            break

        level, confidence, topic, examples, answer = generate_tutor_response(q)

        print("\n=== DETECTED LEVEL ===")
        print(level)
        print("Confidence:", confidence)

        print("\n=== DETECTED TOPIC ===")
        print(topic)

        print("\n=== RETRIEVED EXAMPLES ===")
        for i, row in enumerate(examples.itertuples(index=False), 1):
            print(f"\nExample {i}")
            print("Question:", row.question)
            print("Answer:", row.answer)
            print("Level:", row.level)
            print("Topic:", row.topic)

        print("\n=== TUTOR ANSWER ===")
        print(answer)
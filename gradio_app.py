import os
import re
import json
import pandas as pd
import torch
import torch.nn.functional as F
import gradio as gr
from groq import Groq
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# CONFIG
# =========================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Set GROQ_API_KEY in your environment before running this app.")
MODEL_NAME = "llama-3.3-70b-versatile"
PROFILE_FILE = "learner_profile.json"
DATASET_FILE = "eduagent_dataset.csv"
CLASSIFIER_PATH = "./difficulty_classifier"

client = Groq(api_key=GROQ_API_KEY)

labels = ["beginner", "intermediate", "advanced"]

# Load classifier
tokenizer = DistilBertTokenizer.from_pretrained(CLASSIFIER_PATH)
model = DistilBertForSequenceClassification.from_pretrained(CLASSIFIER_PATH)
model.eval()

# Load dataset
df = pd.read_csv(DATASET_FILE)

# =========================================================
# TEXT HELPERS
# =========================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def filter_by_level(df_level, level):
    df_level = df_level.copy()
    df_level["answer_length"] = df_level["answer"].apply(lambda x: len(str(x).split()))

    if level == "beginner":
        return df_level[df_level["answer_length"] < 80]
    elif level == "intermediate":
        return df_level[(df_level["answer_length"] >= 40) & (df_level["answer_length"] <= 110)]
    elif level == "advanced":
        return df_level[df_level["answer_length"] > 80]
    return df_level

def question_complexity_penalty(text):
    text = clean_text(text)
    penalty = 0.0

    complex_words = [
        "derive", "proof", "prove", "theorem", "theoretical",
        "high dimensional", "non differentiable", "quasi newton",
        "convergence", "subgradient", "vanishing gradient",
        "multivariate", "recurrent neural networks"
    ]

    if len(text.split()) > 18:
        penalty += 0.15

    for word in complex_words:
        if word in text:
            penalty += 0.15

    return penalty

# =========================================================
# MEMORY
# =========================================================
def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "sessions": 0,
        "questions_asked": 0,
        "last_level": "beginner",
        "topics_seen": [],
        "weak_areas": []
    }

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

# =========================================================
# CLASSIFIER
# =========================================================
def predict_level(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = F.softmax(logits, dim=1)
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]
    predicted_label = labels[pred_idx]

    text_lower = text.lower().strip()

    if max(confidence) < 0.6:
        predicted_label = "intermediate"

    simple_patterns = [
        "what is",
        "how does",
        "explain",
        "flow of",
        "in simple terms"
    ]

    advanced_keywords = [
        "compare", "derive", "prove", "analyze", "convergence",
        "theorem", "optimization", "gradient clipping",
        "rmsprop", "adam", "backpropagation", "non-convex"
    ]

    has_simple_pattern = any(p in text_lower for p in simple_patterns)
    has_advanced_keyword = any(k in text_lower for k in advanced_keywords)

    if predicted_label == "advanced" and has_simple_pattern and not has_advanced_keyword:
        predicted_label = "intermediate"

    return predicted_label, confidence

# =========================================================
# RETRIEVER
# =========================================================
def detect_best_topic(user_question, level):
    user_question_clean = clean_text(user_question)

    level_df = df[df["level"].astype(str).str.lower() == level].copy()
    if len(level_df) == 0:
        return None

    topic_texts = (
        level_df.groupby("topic")["question"]
        .apply(lambda qs: " ".join([clean_text(q) for q in qs]))
        .reset_index()
    )

    corpus = [user_question_clean] + topic_texts["question"].tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    user_vec = tfidf_matrix[0:1]
    topic_vecs = tfidf_matrix[1:]

    sims = cosine_similarity(user_vec, topic_vecs).flatten()
    topic_texts["similarity"] = sims

    best_row = topic_texts.sort_values(by="similarity", ascending=False).iloc[0]
    return best_row["topic"]

def retrieve_examples(user_question, level, top_n=2):
    level = str(level).strip().lower()
    user_question_clean = clean_text(user_question)

    best_topic = detect_best_topic(user_question, level)

    filtered = df[df["level"].astype(str).str.lower() == level].copy()

    if best_topic is not None:
        topic_filtered = filtered[
            filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
        ].copy()
        if len(topic_filtered) > 0:
            filtered = topic_filtered

    if len(filtered) == 0:
        return pd.DataFrame(columns=["question", "answer", "level", "topic"])

    filtered = filter_by_level(filtered, level)

    if len(filtered) == 0:
        filtered = df[df["level"].astype(str).str.lower() == level].copy()
        if best_topic is not None:
            topic_filtered = filtered[
                filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
            ].copy()
            if len(topic_filtered) > 0:
                filtered = topic_filtered

    filtered["clean_question"] = filtered["question"].apply(clean_text)

    corpus = [user_question_clean] + filtered["clean_question"].tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    user_vec = tfidf_matrix[0:1]
    dataset_vecs = tfidf_matrix[1:]

    sims = cosine_similarity(user_vec, dataset_vecs).flatten()
    filtered["similarity"] = sims

    filtered["penalty"] = filtered["question"].apply(question_complexity_penalty)
    filtered["final_score"] = filtered["similarity"] - filtered["penalty"]

    filtered = filtered.sort_values(by="final_score", ascending=False)
    top_examples = filtered.head(top_n).copy()

    if len(top_examples) == 0:
        fallback = df[df["level"].astype(str).str.lower() == level].copy()
        if best_topic is not None:
            fallback_topic = fallback[
                fallback["topic"].astype(str).str.lower() == str(best_topic).lower()
            ].copy()
            if len(fallback_topic) > 0:
                fallback = fallback_topic

        top_examples = fallback.sample(min(top_n, len(fallback)), random_state=42)

    return top_examples[["question", "answer", "level", "topic"]]

# =========================================================
# LLM
# =========================================================
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
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content
    return level, confidence, topic, examples, answer

def generate_followup_question(user_question, tutor_answer, level):
    prompt = f"""
A student asked this question:
{user_question}

The tutor answered:
{tutor_answer}

The student's level is:
{level}

Generate ONE short follow-up question to check whether the student understood.
Make it appropriate for the student's level.
Return only the follow-up question.
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

# =========================================================
# UI HELPERS
# =========================================================
def profile_to_markdown(profile):
    return (
        f"**Sessions:** {profile['sessions']}\n\n"
        f"**Questions Asked:** {profile['questions_asked']}\n\n"
        f"**Last Level:** {profile['last_level']}\n\n"
        f"**Topics Seen:** {', '.join(profile['topics_seen']) if profile['topics_seen'] else 'None'}\n\n"
        f"**Weak Areas:** {', '.join(profile['weak_areas']) if profile['weak_areas'] else 'None'}"
    )

def confidence_to_text(conf):
    return (
        f"Beginner: {conf[0]:.3f} | "
        f"Intermediate: {conf[1]:.3f} | "
        f"Advanced: {conf[2]:.3f}"
    )

# =========================================================
# APP FUNCTIONS
# =========================================================
def start_session():
    profile = load_profile()
    profile["sessions"] += 1
    save_profile(profile)
    return profile_to_markdown(profile), []

def ask_eduagent(user_question, chat_history):
    if chat_history is None:
        chat_history = []

    if not user_question or not user_question.strip():
        profile = load_profile()
        return (
            chat_history,   # chatbot
            chat_history,   # state
            "Please enter a question.",
            "",
            "",
            "",
            profile_to_markdown(profile),
            ""
        )

    profile = load_profile()

    level, confidence, topic, examples, answer = generate_tutor_response(user_question)
    followup = generate_followup_question(user_question, answer, level)

    profile["questions_asked"] += 1
    profile["last_level"] = level
    if topic and topic not in profile["topics_seen"]:
        profile["topics_seen"].append(topic)
    save_profile(profile)

    bot_reply = (
        f"**Answer:**\n{answer}\n\n"
        f"**Check your understanding:**\n{followup}"
    )

    chat_history = chat_history + [
        {"role": "user", "content": user_question},
        {"role": "assistant", "content": bot_reply},
    ]

    return (
        chat_history,                    # chatbot
        chat_history,                    # state
        level,
        confidence_to_text(confidence),
        topic,
        followup,
        profile_to_markdown(profile),
        examples_to_markdown(examples),
    )

def clear_chat():
    profile = load_profile()
    return [], [], "", "", "", "", profile_to_markdown(profile), ""

# =========================================================
# UI
# =========================================================
custom_css = """
.gradio-container {
    max-width: 1400px !important;
}
.main-title {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 6px;
}
.sub-title {
    text-align: center;
    font-size: 16px;
    color: #888;
    margin-bottom: 18px;
}
"""

with gr.Blocks() as demo:
    gr.HTML("""
        <div class="main-title">EduAgent — Adaptive AI Tutor</div>
        <div class="sub-title">Learner-aware tutoring with difficulty detection, topic retrieval, memory, and comprehension checking</div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Tutor Conversation", height=500)
            user_input = gr.Textbox(
                label="Ask your AI/ML question",
                placeholder="Example: What is reinforcement learning?",
                lines=3
            )

            with gr.Row():
                ask_btn = gr.Button("Ask EduAgent", variant="primary")
                clear_btn = gr.Button("Clear Chat")

        with gr.Column(scale=2):
            level_box = gr.Textbox(label="Detected Level", interactive=False)
            conf_box = gr.Textbox(label="Confidence Scores", interactive=False)
            topic_box = gr.Textbox(label="Detected Topic", interactive=False)
            followup_box = gr.Textbox(label="Check Your Understanding", lines=4, interactive=False)

            profile_md = gr.Markdown()
            with gr.Accordion("Retrieved Examples", open=False):
                examples_md = gr.Markdown()

    state = gr.State([])

    demo.load(
        fn=start_session,
        inputs=None,
        outputs=[profile_md, state]
    )

    ask_btn.click(
        fn=ask_eduagent,
        inputs=[user_input, state],
        outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md]
    ).then(
        fn=lambda: "",
        inputs=None,
        outputs=[user_input]
    )

    user_input.submit(
        fn=ask_eduagent,
        inputs=[user_input, state],
        outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md]
    ).then(
        fn=lambda: "",
        inputs=None,
        outputs=[user_input]
    )

    clear_btn.click(
        fn=clear_chat,
        inputs=None,
        outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md]
    )

if __name__ == "__main__":
    demo.launch(css=custom_css, theme=gr.themes.Soft())
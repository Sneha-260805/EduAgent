import os
import re
import json
import base64
import hashlib
import hmac
import sqlite3
from datetime import datetime
import pandas as pd
import torch
import torch.nn.functional as F
import gradio as gr
from groq import Groq
from dotenv import load_dotenv
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =========================================================
# CONFIG
# =========================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Set GROQ_API_KEY in your environment or .env file before running this app.")
MODEL_NAME = "llama-3.3-70b-versatile"
DATASET_FILE = "eduagent_dataset.csv"
CLASSIFIER_PATH = "./difficulty_classifier"
DB_FILE = "eduagent.db"

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
# AUTH + PROFILE STORAGE (SQLite)
# =========================================================
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return base64.b64encode(salt + hashed).decode("utf-8")

def verify_password(password, stored_hash):
    try:
        decoded = base64.b64decode(stored_hash.encode("utf-8"))
    except Exception:
        return False
    if len(decoded) < 48:
        return False
    salt = decoded[:16]
    stored = decoded[16:]
    computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200000)
    return hmac.compare_digest(stored, computed)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            sessions INTEGER NOT NULL DEFAULT 0,
            questions_asked INTEGER NOT NULL DEFAULT 0,
            last_level TEXT NOT NULL DEFAULT 'beginner',
            topics_seen TEXT NOT NULL DEFAULT '[]',
            question_history TEXT NOT NULL DEFAULT '[]',
            topic_question_counts TEXT NOT NULL DEFAULT '{}',
            weak_areas TEXT NOT NULL DEFAULT '[]',
            recommended_next_topics TEXT NOT NULL DEFAULT '[]',
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
        """
    )
    cur.execute("PRAGMA table_info(user_profiles)")
    existing_cols = {row[1] for row in cur.fetchall()}
    if "question_history" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN question_history TEXT NOT NULL DEFAULT '[]'")
    if "topic_question_counts" not in existing_cols:
        cur.execute("ALTER TABLE user_profiles ADD COLUMN topic_question_counts TEXT NOT NULL DEFAULT '{}'")
    conn.commit()
    conn.close()

def default_profile():
    return {
        "sessions": 0,
        "questions_asked": 0,
        "last_level": "beginner",
        "topics_seen": [],
        "question_history": [],
        "topic_question_counts": {},
        "weak_areas": [],
        "recommended_next_topics": [],
    }

def create_profile_if_missing(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM user_profiles WHERE user_id = ?", (user_id,))
    existing = cur.fetchone()
    if not existing:
        profile = default_profile()
        cur.execute(
            """
            INSERT INTO user_profiles
            (user_id, sessions, questions_asked, last_level, topics_seen, question_history, topic_question_counts, weak_areas, recommended_next_topics)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                profile["sessions"],
                profile["questions_asked"],
                profile["last_level"],
                json.dumps(profile["topics_seen"]),
                json.dumps(profile["question_history"]),
                json.dumps(profile["topic_question_counts"]),
                json.dumps(profile["weak_areas"]),
                json.dumps(profile["recommended_next_topics"]),
            ),
        )
        conn.commit()
    conn.close()

def load_profile(user_id):
    create_profile_if_missing(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return default_profile()
    return {
        "sessions": int(row["sessions"]),
        "questions_asked": int(row["questions_asked"]),
        "last_level": row["last_level"],
        "topics_seen": json.loads(row["topics_seen"]) if row["topics_seen"] else [],
        "question_history": json.loads(row["question_history"]) if row["question_history"] else [],
        "topic_question_counts": json.loads(row["topic_question_counts"]) if row["topic_question_counts"] else {},
        "weak_areas": json.loads(row["weak_areas"]) if row["weak_areas"] else [],
        "recommended_next_topics": json.loads(row["recommended_next_topics"]) if row["recommended_next_topics"] else [],
    }

def save_profile(user_id, profile):
    create_profile_if_missing(user_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE user_profiles
        SET sessions = ?, questions_asked = ?, last_level = ?, topics_seen = ?, question_history = ?, topic_question_counts = ?, weak_areas = ?, recommended_next_topics = ?
        WHERE user_id = ?
        """,
        (
            profile["sessions"],
            profile["questions_asked"],
            profile["last_level"],
            json.dumps(profile["topics_seen"]),
            json.dumps(profile["question_history"]),
            json.dumps(profile["topic_question_counts"]),
            json.dumps(profile["weak_areas"]),
            json.dumps(profile["recommended_next_topics"]),
            user_id,
        ),
    )
    conn.commit()
    conn.close()

def register_user(name, username, email, password):
    name = (name or "").strip()
    username = (username or "").strip().lower() or None
    email = (email or "").strip().lower()
    password = password or ""
    if not name or not email or len(password) < 6:
        return False, "Name, email, and password (min 6 chars) are required."

    created_at = datetime.utcnow().isoformat() + "Z"
    password_hash = hash_password(password)
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (name, username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, username, email, password_hash, created_at),
        )
        user_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email or username already exists."
    conn.close()
    create_profile_if_missing(user_id)
    return True, "Signup successful. Please log in."

def authenticate_user(identifier, password):
    identifier = (identifier or "").strip().lower()
    password = password or ""
    if not identifier or not password:
        return None, "Enter email/username and password."

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, name, username, email, password_hash, created_at
        FROM users
        WHERE email = ? OR username = ?
        """,
        (identifier, identifier),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return None, "Invalid credentials."
    if not verify_password(password, row["password_hash"]):
        return None, "Invalid credentials."
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "username": row["username"],
        "email": row["email"],
        "created_at": row["created_at"],
    }, "Login successful."

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
# LEARNING PROFILE HELPERS
# =========================================================
def next_level(level):
    order = ["beginner", "intermediate", "advanced"]
    if level not in order:
        return "intermediate"
    idx = order.index(level)
    return order[min(idx + 1, len(order) - 1)]

def update_learning_signals(profile, user_question, detected_level, topic):
    profile["questions_asked"] = int(profile.get("questions_asked", 0)) + 1
    profile["last_level"] = detected_level

    if topic and topic not in profile["topics_seen"]:
        profile["topics_seen"].append(topic)

    history = profile.get("question_history", [])
    history.append({
        "question": user_question.strip(),
        "topic": topic or "unknown",
        "level": detected_level,
        "ts": datetime.utcnow().isoformat() + "Z",
    })
    profile["question_history"] = history[-50:]

    topic_counts = profile.get("topic_question_counts", {})
    if topic:
        topic_counts[topic] = int(topic_counts.get(topic, 0)) + 1
    profile["topic_question_counts"] = topic_counts

    # Weak areas: frequently revisited topics (>=2 asks), top 3.
    weak = [t for t, c in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True) if c >= 2]
    profile["weak_areas"] = weak[:3]

    # Recommended next: weak areas at next level first, then unseen topics.
    nxt = next_level(detected_level)
    level_topics = sorted(
        df[df["level"].astype(str).str.lower() == nxt]["topic"].dropna().astype(str).unique().tolist()
    )
    level_topics_lc = {t.lower(): t for t in level_topics}

    recommendations = []
    for w in profile["weak_areas"]:
        key = str(w).lower()
        if key in level_topics_lc and level_topics_lc[key] not in recommendations:
            recommendations.append(level_topics_lc[key])

    seen_lc = {str(t).lower() for t in profile.get("topics_seen", [])}
    for t in level_topics:
        if t.lower() not in seen_lc and t not in recommendations:
            recommendations.append(t)
        if len(recommendations) >= 5:
            break

    profile["recommended_next_topics"] = recommendations
    return profile

# =========================================================
# UI HELPERS
# =========================================================
def profile_to_markdown(profile):
    recent_q = profile.get("question_history", [])[-3:]
    recent_text = "\n".join([f"- {q['question']}" for q in reversed(recent_q)]) if recent_q else "None"
    return (
        f"**Sessions:** {profile['sessions']}\n\n"
        f"**Questions Asked:** {profile['questions_asked']}\n\n"
        f"**Last Level:** {profile['last_level']}\n\n"
        f"**Topics Seen:** {', '.join(profile['topics_seen']) if profile['topics_seen'] else 'None'}\n\n"
        f"**Weak Areas:** {', '.join(profile['weak_areas']) if profile['weak_areas'] else 'None'}\n\n"
        f"**Recommended Next Topics:** {', '.join(profile['recommended_next_topics']) if profile['recommended_next_topics'] else 'None'}\n\n"
        f"**Recent Questions:**\n{recent_text}"
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
def user_welcome(user):
    if not user:
        return "Not logged in."
    return f"Logged in as **{user['name']}** ({user['email']})"

def handle_signup(name, username, email, password):
    ok, msg = register_user(name, username, email, password)
    if ok:
        return msg, "", "", "", ""
    return msg, name, username, email, ""

def handle_login(identifier, password):
    user, msg = authenticate_user(identifier, password)
    if not user:
        return (
            msg,
            None,
            "",
            [],
            [],
            "",
            "",
            "",
            "",
            gr.update(visible=True),
            gr.update(visible=False),
        )

    profile = load_profile(user["user_id"])
    profile["sessions"] += 1
    save_profile(user["user_id"], profile)
    return (
        msg,
        user,
        user_welcome(user),
        [],
        [],
        "",
        "",
        "",
        profile_to_markdown(profile),
        gr.update(visible=False),
        gr.update(visible=True),
    )

def handle_logout():
    return (
        "Logged out.",
        None,
        "",
        [],
        [],
        "",
        "",
        "",
        "",
        gr.update(visible=True),
        gr.update(visible=False),
    )

def ask_eduagent(user_question, chat_history, user):
    if chat_history is None:
        chat_history = []
    if not user:
        return (
            chat_history,
            chat_history,
            "Please login first.",
            "",
            "",
            "",
            "",
            "",
        )

    if not user_question or not user_question.strip():
        profile = load_profile(user["user_id"])
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

    profile = load_profile(user["user_id"])

    level, confidence, topic, examples, answer = generate_tutor_response(user_question)
    followup = generate_followup_question(user_question, answer, level)

    profile = update_learning_signals(
        profile=profile,
        user_question=user_question,
        detected_level=level,
        topic=topic,
    )
    save_profile(user["user_id"], profile)

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
    return [], [], "", "", "", "", "", ""

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
    auth_status = gr.Markdown("")
    user_state = gr.State(None)
    state = gr.State([])

    with gr.Column(visible=True) as auth_section:
        with gr.Tab("Login"):
            login_identifier = gr.Textbox(label="Email or Username")
            login_password = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login", variant="primary")

        with gr.Tab("Signup"):
            signup_name = gr.Textbox(label="Full Name")
            signup_username = gr.Textbox(label="Username (optional)")
            signup_email = gr.Textbox(label="Email")
            signup_password = gr.Textbox(label="Password (min 6 chars)", type="password")
            signup_btn = gr.Button("Create Account")

    with gr.Column(visible=False) as app_section:
        welcome_md = gr.Markdown("")
        logout_btn = gr.Button("Logout")

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

    signup_btn.click(
        fn=handle_signup,
        inputs=[signup_name, signup_username, signup_email, signup_password],
        outputs=[auth_status, signup_name, signup_username, signup_email, signup_password],
    )

    login_btn.click(
        fn=handle_login,
        inputs=[login_identifier, login_password],
        outputs=[
            auth_status, user_state, welcome_md, chatbot, state, level_box, conf_box, topic_box,
            profile_md, auth_section, app_section
        ],
    ).then(
        fn=lambda: ("", ""),
        inputs=None,
        outputs=[login_identifier, login_password],
    )

    logout_btn.click(
        fn=handle_logout,
        inputs=None,
        outputs=[
            auth_status, user_state, welcome_md, chatbot, state, level_box, conf_box, topic_box,
            profile_md, auth_section, app_section
        ],
    )

    ask_btn.click(
        fn=ask_eduagent,
        inputs=[user_input, state, user_state],
        outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md]
    ).then(
        fn=lambda: "",
        inputs=None,
        outputs=[user_input]
    )

    user_input.submit(
        fn=ask_eduagent,
        inputs=[user_input, state, user_state],
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
    init_db()
    demo.launch(css=custom_css, theme=gr.themes.Soft())
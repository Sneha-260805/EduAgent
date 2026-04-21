import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_best_topic(user_question, level, df):
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

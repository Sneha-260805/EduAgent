import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import DATASET_FILE
from ml.topic_detector import clean_text, detect_best_topic


df = pd.read_csv(DATASET_FILE)


def filter_by_level(df_level, level):
    df_level = df_level.copy()
    df_level["answer_length"] = df_level["answer"].apply(lambda x: len(str(x).split()))

    if level == "beginner":
        return df_level[df_level["answer_length"] < 80]
    if level == "intermediate":
        return df_level[(df_level["answer_length"] >= 40) & (df_level["answer_length"] <= 110)]
    if level == "advanced":
        return df_level[df_level["answer_length"] > 80]
    return df_level


def question_complexity_penalty(text):
    text = clean_text(text)
    penalty = 0.0
    complex_words = [
        "derive", "proof", "prove", "theorem", "theoretical",
        "high dimensional", "non differentiable", "quasi newton",
        "convergence", "subgradient", "vanishing gradient",
        "multivariate", "recurrent neural networks",
    ]
    if len(text.split()) > 18:
        penalty += 0.15
    for word in complex_words:
        if word in text:
            penalty += 0.15
    return penalty


def retrieve_examples(user_question, level, top_n=2):
    level = str(level).strip().lower()
    user_question_clean = clean_text(user_question)

    best_topic = detect_best_topic(user_question, level, df)
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

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import DATASET_FILE
from ml.topic_detector import clean_text, detect_best_topic, expand_topic_aliases


df = pd.read_csv(DATASET_FILE)
_RETRIEVAL_INDEX_CACHE = {}


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


def _retrieval_cache_key(level: str, topic: str | None):
    return (
        len(df),
        str(level).strip().lower(),
        str(topic).strip().lower() if topic is not None else "",
    )


def _build_retrieval_index(level: str, best_topic: str | None):
    filtered = df[df["level"].astype(str).str.lower() == level].copy()

    if best_topic is not None:
        topic_filtered = filtered[
            filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
        ].copy()
        if len(topic_filtered) > 0:
            filtered = topic_filtered

    if len(filtered) == 0:
        return filtered, None, None

    filtered = filter_by_level(filtered, level)

    if len(filtered) == 0:
        filtered = df[df["level"].astype(str).str.lower() == level].copy()
        if best_topic is not None:
            topic_filtered = filtered[
                filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
            ].copy()
            if len(topic_filtered) > 0:
                filtered = topic_filtered

    if len(filtered) == 0:
        return filtered, None, None

    filtered["clean_question"] = filtered["question"].apply(clean_text)
    filtered["penalty"] = filtered["question"].apply(question_complexity_penalty)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    dataset_matrix = vectorizer.fit_transform(filtered["clean_question"].tolist())
    return filtered.reset_index(drop=True), vectorizer, dataset_matrix


def get_retrieval_index(level: str, topic: str | None):
    key = _retrieval_cache_key(level, topic)
    if key not in _RETRIEVAL_INDEX_CACHE:
        _RETRIEVAL_INDEX_CACHE[key] = _build_retrieval_index(level, topic)
    return _RETRIEVAL_INDEX_CACHE[key]


def retrieve_examples(user_question, level, top_n=2):
    """
    Retrieve examples using a cached lexical retrieval index.

    This is intentionally described as TF-IDF example retrieval, not full dense
    vector RAG. The index is built once per level/topic and reused across
    queries to avoid repeated vectorizer fitting.
    """
    level = str(level).strip().lower()
    user_question_clean = expand_topic_aliases(clean_text(user_question))

    best_topic = detect_best_topic(user_question, level, df)
    filtered, vectorizer, dataset_vecs = get_retrieval_index(level, best_topic)

    if len(filtered) == 0 or vectorizer is None or dataset_vecs is None:
        return pd.DataFrame(columns=["question", "answer", "level", "topic"])

    user_vec = vectorizer.transform([user_question_clean])
    sims = cosine_similarity(user_vec, dataset_vecs).flatten()
    scored = filtered.copy()
    scored["similarity"] = sims

    scored["final_score"] = scored["similarity"] - scored["penalty"]

    scored = scored.sort_values(by="final_score", ascending=False)
    top_examples = scored.head(top_n).copy()

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

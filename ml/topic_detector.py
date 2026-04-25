import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_TOPIC_INDEX_CACHE = {}
TOPIC_ALIASES = {
    "large language models": [
        "llm",
        "llms",
        "large language model",
        "large language models",
        "gpt",
        "chatgpt",
    ],
    "natural language processing": [
        "nlp",
        "natural language processing",
    ],
    "retrieval augmented generation": [
        "rag",
        "retrieval augmented generation",
        "retrieval-augmented generation",
    ],
    "vector databases": [
        "vector db",
        "vector database",
        "vector databases",
        "embedding database",
    ],
    "convolutional neural networks": [
        "cnn",
        "cnns",
        "convolutional neural network",
        "convolutional neural networks",
    ],
    "recurrent neural networks": [
        "rnn",
        "rnns",
        "recurrent neural network",
        "recurrent neural networks",
    ],
    "generative adversarial networks": [
        "gan",
        "gans",
        "generative adversarial network",
        "generative adversarial networks",
    ],
}


def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _available_topic_lookup(df: pd.DataFrame):
    return {str(topic).lower(): topic for topic in df["topic"].dropna().unique()}


def _alias_topic(user_question_clean: str, df: pd.DataFrame):
    topic_lookup = _available_topic_lookup(df)
    padded_question = f" {user_question_clean} "
    for canonical_topic, aliases in TOPIC_ALIASES.items():
        if canonical_topic not in topic_lookup:
            continue
        for alias in aliases:
            alias_clean = clean_text(alias)
            if f" {alias_clean} " in padded_question:
                return topic_lookup[canonical_topic]
    return None


def expand_topic_aliases(text: str) -> str:
    expanded_terms = []
    padded_text = f" {text} "
    for canonical_topic, aliases in TOPIC_ALIASES.items():
        canonical_clean = clean_text(canonical_topic)
        for alias in aliases:
            alias_clean = clean_text(alias)
            if re.search(rf"\b{re.escape(alias_clean)}\b", padded_text):
                expanded_terms.append(canonical_clean)
                break
    if not expanded_terms:
        return text
    return re.sub(r"\s+", " ", f"{text} {' '.join(sorted(set(expanded_terms)))}").strip()


def _df_cache_key(df: pd.DataFrame, level: str):
    return (
        id(df),
        len(df),
        str(level).strip().lower(),
        tuple(df.columns),
    )


def _build_topic_index(level, df):
    level_df = df[df["level"].astype(str).str.lower() == level].copy()
    if len(level_df) == 0:
        return None

    topic_texts = (
        level_df.groupby("topic")["question"]
        .apply(lambda qs: " ".join([clean_text(q) for q in qs]))
        .reset_index()
    )
    topic_texts["question"] = topic_texts.apply(
        lambda row: f"{clean_text(row['topic'])} {row['question']}",
        axis=1,
    )

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    topic_matrix = vectorizer.fit_transform(topic_texts["question"].tolist())
    return topic_texts, vectorizer, topic_matrix


def get_topic_index(level, df):
    level = str(level).strip().lower()
    key = _df_cache_key(df, level)
    if key not in _TOPIC_INDEX_CACHE:
        _TOPIC_INDEX_CACHE[key] = _build_topic_index(level, df)
    return _TOPIC_INDEX_CACHE[key]


def detect_best_topic(user_question, level, df):
    """
    Detect the closest topic using a cached TF-IDF topic index.

    This is still lexical retrieval, not dense semantic RAG, but it avoids
    refitting a vectorizer on every single query.
    """
    user_question_clean = clean_text(user_question)
    alias_topic = _alias_topic(user_question_clean, df)
    user_question_clean = expand_topic_aliases(user_question_clean)
    index = get_topic_index(level, df)
    if index is None:
        return alias_topic

    topic_texts, vectorizer, topic_matrix = index
    user_vec = vectorizer.transform([user_question_clean])
    sims = cosine_similarity(user_vec, topic_matrix).flatten()
    scored_topics = topic_texts.copy()
    scored_topics["similarity"] = sims

    if alias_topic is not None:
        scored_topics.loc[
            scored_topics["topic"].astype(str).str.lower() == str(alias_topic).lower(),
            "similarity",
        ] += 0.35

    if scored_topics["similarity"].max() <= 0:
        return alias_topic

    best_row = scored_topics.sort_values(by="similarity", ascending=False).iloc[0]
    return best_row["topic"]

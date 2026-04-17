import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load dataset once
df = pd.read_csv("eduagent_dataset.csv")

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

def detect_best_topic(user_question, level):
    """
    First find which topic is most relevant to the user's question.
    """
    user_question_clean = clean_text(user_question)

    level_df = df[df["level"].astype(str).str.lower() == level].copy()
    if len(level_df) == 0:
        return None

    # Represent each topic using all questions in that topic
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

def retrieve_examples(user_question, level, top_n=3):
    level = str(level).strip().lower()
    user_question_clean = clean_text(user_question)

    # Step 1: detect best topic
    best_topic = detect_best_topic(user_question, level)

    # Step 2: filter by level + detected topic
    filtered = df[df["level"].astype(str).str.lower() == level].copy()

    if best_topic is not None:
        topic_filtered = filtered[
            filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
        ].copy()

        if len(topic_filtered) > 0:
            filtered = topic_filtered

    if len(filtered) == 0:
        return pd.DataFrame(columns=["question", "answer", "level", "topic"])

    # Step 3: apply answer-length control
    filtered = filter_by_level(filtered, level)

    if len(filtered) == 0:
        filtered = df[df["level"].astype(str).str.lower() == level].copy()
        if best_topic is not None:
            topic_filtered = filtered[
                filtered["topic"].astype(str).str.lower() == str(best_topic).lower()
            ].copy()
            if len(topic_filtered) > 0:
                filtered = topic_filtered

    # Step 4: semantic similarity within chosen topic
    filtered["clean_question"] = filtered["question"].apply(clean_text)

    corpus = [user_question_clean] + filtered["clean_question"].tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(corpus)

    user_vec = tfidf_matrix[0:1]
    dataset_vecs = tfidf_matrix[1:]

    sims = cosine_similarity(user_vec, dataset_vecs).flatten()
    filtered["similarity"] = sims

    # Step 5: apply complexity penalty
    filtered["penalty"] = filtered["question"].apply(question_complexity_penalty)
    filtered["final_score"] = filtered["similarity"] - filtered["penalty"]

    # Step 6: sort
    filtered = filtered.sort_values(by="final_score", ascending=False)

    top_examples = filtered.head(top_n).copy()

    # Step 7: fallback
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

if __name__ == "__main__":
    while True:
        q = input("\nEnter a student question (or quit): ").strip()
        if q.lower() == "quit":
            break

        level = input("Enter predicted level (beginner/intermediate/advanced): ").strip().lower()

        best_topic = detect_best_topic(q, level)
        print(f"\nDetected Topic: {best_topic}")

        results = retrieve_examples(q, level, top_n=3)

        print("\n=== Retrieved Examples ===")
        for i, row in enumerate(results.itertuples(index=False), 1):
            print(f"\nExample {i}")
            print("Question:", row.question)
            print("Answer:", row.answer)
            print("Level:", row.level)
            print("Topic:", row.topic)
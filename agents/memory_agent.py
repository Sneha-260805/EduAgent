from datetime import datetime
from ml.retriever import df


def next_level(level):
    order = ["beginner", "intermediate", "advanced"]
    if level not in order:
        return "intermediate"
    idx = order.index(level)
    return order[min(idx + 1, len(order) - 1)]


def build_memory_hint(profile, topic):
    if not topic:
        return "No prior topic memory."
    topic_counts = profile.get("topic_question_counts", {})
    count = int(topic_counts.get(topic, 0))
    seen = topic in profile.get("topics_seen", [])
    if count >= 2:
        return (
            f"Topic '{topic}' has come up repeatedly ({count} times). "
            "Treat as possible weak area; avoid repeating a full beginner intro and focus on targeted clarification."
        )
    if seen:
        return (
            f"Topic '{topic}' has been seen before. "
            "Skip restarting from scratch; briefly recap then continue from prior understanding."
        )
    return f"Topic '{topic}' appears new for this learner. Start with a concise onboarding explanation."


def update_learning_signals(profile, user_question, detected_level, topic):
    profile["questions_asked"] = int(profile.get("questions_asked", 0)) + 1
    profile["last_level"] = detected_level

    if topic and topic not in profile["topics_seen"]:
        profile["topics_seen"].append(topic)

    history = profile.get("question_history", [])
    history.append(
        {
            "question": user_question.strip(),
            "topic": topic or "unknown",
            "level": detected_level,
            "ts": datetime.utcnow().isoformat() + "Z",
        }
    )
    profile["question_history"] = history[-50:]

    topic_counts = profile.get("topic_question_counts", {})
    if topic:
        topic_counts[topic] = int(topic_counts.get(topic, 0)) + 1
    profile["topic_question_counts"] = topic_counts

    weak = [t for t, c in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True) if c >= 2]
    profile["weak_areas"] = weak[:3]

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

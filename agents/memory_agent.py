from typing import Dict, List


def ensure_profile_structure(profile: Dict) -> Dict:
    """
    Ensure all expected keys exist in the learner profile.
    """
    if profile is None:
        profile = {}

    # Backward-compat normalization for older profile shapes.
    if isinstance(profile.get("weak_areas"), list):
        # Old shape was a list of weak topics; convert to topic->concept-list map.
        profile["weak_areas"] = {str(topic): [] for topic in profile.get("weak_areas", []) if topic}

    if "topic_counts" not in profile and isinstance(profile.get("topic_question_counts"), dict):
        profile["topic_counts"] = dict(profile.get("topic_question_counts", {}))

    # Type guards: ensure dict/list fields are in expected form.
    if not isinstance(profile.get("topic_counts"), dict):
        profile["topic_counts"] = {}
    if not isinstance(profile.get("weak_areas"), dict):
        profile["weak_areas"] = {}
    if not isinstance(profile.get("mastery"), dict):
        profile["mastery"] = {}
    if not isinstance(profile.get("used_explanations"), dict):
        profile["used_explanations"] = {}
    if not isinstance(profile.get("topics_seen"), list):
        profile["topics_seen"] = []
    if not isinstance(profile.get("recommended_next_topics"), list):
        profile["recommended_next_topics"] = []
    if not isinstance(profile.get("level_history"), list):
        profile["level_history"] = []

    profile.setdefault("sessions", 0)
    profile.setdefault("questions_asked", 0)
    profile.setdefault("last_level", "beginner")
    profile.setdefault("level_history", [])
    profile.setdefault("topics_seen", [])
    profile.setdefault("topic_counts", {})
    profile.setdefault("weak_areas", {})
    profile.setdefault("mastery", {})
    profile.setdefault("used_explanations", {})
    profile.setdefault("recommended_next_topics", [])
    return profile


def update_profile_after_question(profile: Dict, topic: str, level: str) -> Dict:
    """
    Update learner profile immediately after a question is asked / answered.
    """
    profile = ensure_profile_structure(profile)

    profile["questions_asked"] += 1
    profile["last_level"] = level
    profile["level_history"].append(level)

    if topic and topic not in profile["topics_seen"]:
        profile["topics_seen"].append(topic)

    if topic:
        profile["topic_counts"][topic] = profile["topic_counts"].get(topic, 0) + 1

    return profile


def update_profile_after_evaluation(profile: Dict, topic: str, evaluation: Dict) -> Dict:
    """
    Update weak areas and mastery based on learner's follow-up response evaluation.
    """
    profile = ensure_profile_structure(profile)

    profile["weak_areas"].setdefault(topic, [])
    profile["mastery"].setdefault(topic, 0.5)

    understanding = evaluation.get("understanding_level", "partial")
    weak_concepts = evaluation.get("weak_concepts", [])

    # Update mastery score
    current_mastery = profile["mastery"].get(topic, 0.5)

    if understanding == "good":
        current_mastery = min(1.0, current_mastery + 0.10)
    elif understanding == "partial":
        current_mastery = max(0.0, current_mastery - 0.05)
    else:  # poor
        current_mastery = max(0.0, current_mastery - 0.15)

    profile["mastery"][topic] = round(current_mastery, 2)

    # Merge weak concepts
    existing = set(profile["weak_areas"].get(topic, []))
    for concept in weak_concepts:
        if concept and isinstance(concept, str):
            existing.add(concept.strip())

    # Also treat repeated topic revisits as a weakness signal
    if profile["topic_counts"].get(topic, 0) >= 3 and not weak_concepts:
        existing.add("core understanding")

    profile["weak_areas"][topic] = sorted(list(existing))

    # Refresh recommendations
    profile["recommended_next_topics"] = recommend_next_topics(profile, current_topic=topic)

    return profile


def record_used_explanation(profile: Dict, topic: str, explanation_tag: str) -> Dict:
    """
    Optionally store which explanation style/analogy was already used.
    """
    profile = ensure_profile_structure(profile)
    profile["used_explanations"].setdefault(topic, [])

    if explanation_tag and explanation_tag not in profile["used_explanations"][topic]:
        profile["used_explanations"][topic].append(explanation_tag)

    return profile


def build_memory_hint(profile: Dict, topic: str) -> str:
    """
    Build a personalization hint for the Tutor Agent prompt.
    """
    profile = ensure_profile_structure(profile)

    hints: List[str] = []

    topic_count = profile["topic_counts"].get(topic, 0)
    weak_areas = profile["weak_areas"].get(topic, [])
    mastery = profile["mastery"].get(topic, 0.5)
    used_explanations = profile["used_explanations"].get(topic, [])

    if topic_count > 1:
        hints.append(
            "The learner has seen this topic before. Do not restart with the exact same beginner introduction."
        )

    if weak_areas:
        hints.append(
            f"The learner has previously struggled with: {', '.join(weak_areas)}. Address these concepts carefully."
        )

    if mastery < 0.4:
        hints.append(
            "The learner appears weak in this topic. Use simpler wording, intuition, and one concrete example."
        )
    elif mastery > 0.75:
        hints.append(
            "The learner appears comfortable with this topic. You may go slightly deeper than before."
        )

    if used_explanations:
        hints.append(
            f"Avoid repeating the exact same prior explanation style if possible. Previously used: {', '.join(used_explanations)}."
        )

    if not hints:
        hints.append("No strong prior history for this topic. Start with a clear explanation.")

    return "\n".join(hints)


def recommend_next_topics(profile: Dict, current_topic: str = "") -> List[str]:
    """
    Very simple recommendation logic for now.
    """
    profile = ensure_profile_structure(profile)

    weak_areas = profile.get("weak_areas", {})
    mastery = profile.get("mastery", {})

    recommendations = []

    # Prioritize weak topics first
    weak_topics = [topic for topic, concepts in weak_areas.items() if concepts]
    for topic in weak_topics:
        if topic not in recommendations and topic != current_topic:
            recommendations.append(topic)

    # Then add low-mastery topics
    low_mastery_topics = sorted(mastery.items(), key=lambda x: x[1])
    for topic, score in low_mastery_topics:
        if score < 0.6 and topic not in recommendations and topic != current_topic:
            recommendations.append(topic)

    # Keep it short
    return recommendations[:2]
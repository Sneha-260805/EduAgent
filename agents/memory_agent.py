from typing import Dict, List


MASTERY_INITIAL_SCORE = 0.5
MASTERY_DELTA_GOOD = 0.10
MASTERY_DELTA_PARTIAL = -0.05
MASTERY_DELTA_POOR = -0.15


def _safe_mastery_score(value, default: float = MASTERY_INITIAL_SCORE) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
    profile.setdefault("last_evaluation", {})
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

    Mastery is currently a simple heuristic score, not a formal cognitive model
    such as Bayesian Knowledge Tracing. The deltas are intentionally named so
    they can be tuned or replaced later without hiding "magic numbers" inside
    the update logic.
    """
    profile = ensure_profile_structure(profile)

    profile["weak_areas"].setdefault(topic, [])
    profile["mastery"].setdefault(topic, MASTERY_INITIAL_SCORE)

    understanding = evaluation.get("understanding_level", "partial")
    weak_concepts = evaluation.get("weak_concepts", [])

    # Update mastery score
    current_mastery = _safe_mastery_score(profile["mastery"].get(topic, MASTERY_INITIAL_SCORE))

    if understanding == "good":
        current_mastery = min(1.0, current_mastery + MASTERY_DELTA_GOOD)
    elif understanding == "partial":
        current_mastery = max(0.0, current_mastery + MASTERY_DELTA_PARTIAL)
    else:  # poor
        current_mastery = max(0.0, current_mastery + MASTERY_DELTA_POOR)

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

def update_last_evaluation(profile: dict, topic: str, evaluation: dict) -> dict:
    """
    Store the most recent evaluation result so the Tutor Agent can adapt next time.
    """
    profile = ensure_profile_structure(profile)
    profile["last_evaluation"] = {
        "topic": topic,
        "understanding_level": evaluation.get("understanding_level", "partial"),
        "weak_concepts": evaluation.get("weak_concepts", []),
        "feedback": evaluation.get("feedback", ""),
        "recommended_action": evaluation.get("recommended_action", "give more practice"),
    }
    return profile


def build_evaluation_strategy_hint(profile: dict, topic: str) -> str:
    """
    Build a tutoring strategy hint from the most recent evaluator output.
    Only apply if the last evaluation belongs to the same topic.
    """
    profile = ensure_profile_structure(profile)

    last_eval = profile.get("last_evaluation", {})
    if not last_eval:
        return ""

    if last_eval.get("topic") != topic:
        return ""

    understanding = last_eval.get("understanding_level", "partial")
    weak_concepts = last_eval.get("weak_concepts", [])
    action = last_eval.get("recommended_action", "")

    hints = []

    if understanding == "poor":
        hints.append(
            "Teaching mode: remedial. "
            "The learner did not understand the previous explanation. "
            "Do NOT repeat the same analogy-driven explanation. "
            "Re-teach the concept from scratch using very simple wording, "
            "one tiny concrete example, and a short step-by-step explanation."
        )
    elif understanding == "partial":
        hints.append(
            "Teaching mode: clarification. "
            "The learner understood partially. "
            "Do not repeat the whole answer. "
            "Briefly restate the core idea, then focus on the confusing part with one clear example."
        )
    elif understanding == "good":
        hints.append(
            "Teaching mode: advance. "
            "The learner understood the previous explanation well. "
            "Do not repeat the full beginner introduction. "
            "Give a slightly deeper explanation and connect it to the next related concept."
        )
    else:
        hints.append("Teaching mode: default.")

    if weak_concepts:
        hints.append(
            f"Focus mainly on these weak concepts first: {', '.join(weak_concepts)}."
        )

    if action == "give easier example":
        hints.append(
            "Use one very easy real-world or numeric example."
        )
    elif action == "re-explain":
        hints.append(
            "Explain from scratch in the simplest possible way."
        )
    elif action == "give more practice":
        hints.append(
            "After explaining, add one short practice-style check."
        )
    elif action == "advance":
        hints.append(
            "After the explanation, connect to the next topic."
        )

    return " ".join(hints)

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
    mastery = _safe_mastery_score(profile["mastery"].get(topic, MASTERY_INITIAL_SCORE))
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
    low_mastery_topics = sorted(
        mastery.items(),
        key=lambda item: _safe_mastery_score(item[1], default=1.0),
    )
    for topic, score in low_mastery_topics:
        score = _safe_mastery_score(score, default=1.0)
        if score < 0.6 and topic not in recommendations and topic != current_topic:
            recommendations.append(topic)

    # Keep it short
    return recommendations[:2]

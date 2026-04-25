import json
from html import escape

import gradio as gr
import matplotlib.pyplot as plt

from auth.auth_service import signup_user, login_user
from db.profile_repository import load_profile, save_profile
from db.sqlite_store import init_db
from agents.tutor_agent import generate_tutor_response
from agents.evaluator_agent import (
    generate_followup_question,
    evaluate_followup_response,
)
from agents.memory_agent import (
    ensure_profile_structure,
    update_profile_after_question,
    update_profile_after_evaluation,
    update_last_evaluation,
    build_memory_hint,
    build_evaluation_strategy_hint,
)
from app.ui import build_ui, build_demo


def confidence_to_text(conf):
    return (
        f"Beginner: {conf[0]:.3f} | "
        f"Intermediate: {conf[1]:.3f} | "
        f"Advanced: {conf[2]:.3f}"
    )


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


def profile_to_markdown(profile):
    profile = ensure_profile_structure(profile)

    def _list_items(values):
        values = [escape(str(value)) for value in values if value]
        if not values:
            return "<p>None yet</p>"
        return "<ul>" + "".join(f"<li>{value}</li>" for value in values) + "</ul>"

    def _topic_map_items(topic_map):
        rows = []
        for topic, values in topic_map.items():
            if values:
                concepts = ", ".join(escape(str(value)) for value in values)
                rows.append(f"<li><strong>{escape(str(topic))}</strong>: {concepts}</li>")
        if not rows:
            return "<p>None yet</p>"
        return "<ul>" + "".join(rows) + "</ul>"

    weak_areas_lines = []
    for topic, concepts in profile.get("weak_areas", {}).items():
        if concepts:
            weak_areas_lines.append((topic, concepts))

    mastery_lines = []
    for topic, score in profile.get("mastery", {}).items():
        try:
            score_text = f"{float(score):.2f}"
        except (TypeError, ValueError):
            score_text = escape(str(score))
        mastery_lines.append(f"{escape(str(topic))}: {score_text}")

    recommendations = profile.get("recommended_next_topics", [])
    topics_seen = profile.get("topics_seen", [])

    weak_areas = _topic_map_items(dict(weak_areas_lines))

    return (
        "<div class='profile-grid'>"
        "<div class='profile-card'>"
        "<h4>Activity</h4>"
        f"<p><strong>Sessions:</strong> {profile.get('sessions', 0)}<br>"
        f"<strong>Questions Asked:</strong> {profile.get('questions_asked', 0)}<br>"
        f"<strong>Last Level:</strong> {escape(str(profile.get('last_level', 'beginner')))}</p>"
        "</div>"
        "<div class='profile-card'>"
        "<h4>Topics Seen</h4>"
        f"{_list_items(topics_seen)}"
        "</div>"
        "<div class='profile-card wide-card'>"
        "<h4>Weak Areas</h4>"
        f"{weak_areas}"
        "</div>"
        "<div class='profile-card'>"
        "<h4>Mastery</h4>"
        f"{_list_items(mastery_lines)}"
        "</div>"
        "<div class='profile-card'>"
        "<h4>Recommended Next Topics</h4>"
        f"{_list_items(recommendations)}"
        "</div>"
        "</div>"
    )


def format_evaluation_markdown(evaluation: dict):
    level = (evaluation.get("understanding_level", "partial") or "partial").lower()
    if level == "good":
        css_class = "eval-good"
        label = "GOOD"
    elif level == "poor":
        css_class = "eval-poor"
        label = "POOR"
    else:
        css_class = "eval-partial"
        label = "PARTIAL"

    weak_concepts = evaluation.get("weak_concepts", [])
    weak_text = ", ".join(escape(str(item)) for item in weak_concepts) if weak_concepts else "None"

    return (
        f"<div class='eval-card {css_class}'>"
        f"<h3>Understanding Level: {label}</h3>"
        f"<p><strong>Weak Concepts:</strong> {weak_text}</p>"
        f"<p><strong>Feedback:</strong> {escape(str(evaluation.get('feedback', '')))}</p>"
        f"<p><strong>Recommended Action:</strong> {escape(str(evaluation.get('recommended_action', '')))}</p>"
        "</div>"
    )


CHART_BG = "#0b1120"
CHART_PANEL = "#111827"
CHART_TEXT = "#e5e7eb"
CHART_MUTED = "#94a3b8"
CHART_GRID = "#334155"


def _style_dark_axis(ax, title: str):
    ax.set_facecolor(CHART_PANEL)
    ax.set_title(title, fontsize=13, fontweight="bold", color="#f8fafc", pad=12)
    ax.tick_params(axis="x", colors=CHART_MUTED, labelsize=9, rotation=25)
    ax.tick_params(axis="y", colors=CHART_MUTED, labelsize=9)
    ax.yaxis.label.set_color(CHART_MUTED)
    ax.grid(axis="y", color=CHART_GRID, alpha=0.34, linewidth=0.8)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#243044")


def _placeholder_chart(title: str, message: str):
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.patch.set_facecolor(CHART_BG)
    ax.set_facecolor(CHART_PANEL)
    ax.axis("off")
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color=CHART_MUTED)
    ax.set_title(title, fontsize=13, fontweight="bold", color="#f8fafc", pad=12)
    fig.tight_layout(pad=1.4)
    return fig


def build_mastery_chart(profile: dict):
    profile = ensure_profile_structure(profile)
    mastery = profile.get("mastery", {})
    if not mastery:
        return _placeholder_chart("Mastery by Topic", "No mastery data yet.\nAsk and evaluate a few questions.")

    chart_rows = []
    for topic, score in mastery.items():
        try:
            chart_rows.append((topic, float(score)))
        except (TypeError, ValueError):
            continue
    if not chart_rows:
        return _placeholder_chart("Mastery by Topic", "Mastery data is not numeric yet.")

    topics = [topic for topic, _score in chart_rows]
    scores = [score for _topic, score in chart_rows]

    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.patch.set_facecolor(CHART_BG)
    bars = ax.bar(topics, scores, color="#14b8a6", edgecolor="#99f6e4", linewidth=0.8)
    ax.bar_label(bars, fmt="%.2f", padding=3, color=CHART_TEXT, fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Mastery Score")
    _style_dark_axis(ax, "Mastery by Topic")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=1.4)
    return fig


def build_topic_revisit_chart(profile: dict):
    profile = ensure_profile_structure(profile)
    topic_counts = profile.get("topic_counts", {})
    if not topic_counts:
        return _placeholder_chart("Topic Revisit Count", "No topic revisit data yet.")

    chart_rows = []
    for topic, count in topic_counts.items():
        try:
            chart_rows.append((topic, int(count)))
        except (TypeError, ValueError):
            continue
    if not chart_rows:
        return _placeholder_chart("Topic Revisit Count", "Topic revisit data is not numeric yet.")

    topics = [topic for topic, _count in chart_rows]
    counts = [count for _topic, count in chart_rows]

    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.patch.set_facecolor(CHART_BG)
    bars = ax.bar(topics, counts, color="#3b82f6", edgecolor="#93c5fd", linewidth=0.8)
    ax.bar_label(bars, padding=3, color=CHART_TEXT, fontsize=8)
    if counts:
        ax.set_ylim(0, max(counts) * 1.22 + 0.2)
    ax.set_ylabel("Questions/Revisits")
    _style_dark_axis(ax, "Topic Revisit Count")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=1.4)
    return fig


def build_weak_concepts_chart(profile: dict):
    profile = ensure_profile_structure(profile)
    weak_areas = profile.get("weak_areas", {})
    counts = {topic: len(concepts or []) for topic, concepts in weak_areas.items() if concepts}
    if not counts:
        return _placeholder_chart("Weak Concept Count by Topic", "No weak-concept signals yet.")

    topics = list(counts.keys())
    values = [counts[t] for t in topics]

    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    fig.patch.set_facecolor(CHART_BG)
    bars = ax.bar(topics, values, color="#f59e0b", edgecolor="#fde68a", linewidth=0.8)
    ax.bar_label(bars, padding=3, color=CHART_TEXT, fontsize=8)
    if values:
        ax.set_ylim(0, max(values) * 1.22 + 0.2)
    ax.set_ylabel("Weak Concept Count")
    _style_dark_axis(ax, "Weak Concept Count by Topic")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(pad=1.4)
    return fig


def build_system_insights_markdown(
    level: str = "",
    confidence_text: str = "",
    topic: str = "",
    profile: dict | None = None,
):
    profile = ensure_profile_structure(profile or {})
    memory_hint = build_memory_hint(profile, topic) if topic else "No topic yet."
    eval_hint = build_evaluation_strategy_hint(profile, topic) if topic else "No topic yet."
    last_eval = profile.get("last_evaluation", {})
    last_eval_summary = "No evaluation yet."
    if last_eval:
        last_eval_summary = (
            f"{last_eval.get('understanding_level', 'partial')} on "
            f"{last_eval.get('topic', 'unknown topic')}: "
            f"{last_eval.get('recommended_action', 'give more practice')}"
        )

    return (
        "<div class='insight-block'>"
        "<h4>Pipeline Signals</h4>"
        f"<p><strong>Predicted Level:</strong> {escape(str(level or 'N/A'))}<br>"
        f"<strong>Confidence Scores:</strong> {escape(str(confidence_text or 'N/A'))}<br>"
        f"<strong>Detected Topic:</strong> {escape(str(topic or 'N/A'))}</p>"
        "</div>"
        "<div class='insight-block'>"
        "<h4>Memory Hint / Tutor Strategy</h4>"
        f"<p>{escape(memory_hint)}</p>"
        "</div>"
        "<div class='insight-block'>"
        "<h4>Last Evaluation Summary</h4>"
        f"<p>{escape(last_eval_summary)}</p>"
        "</div>"
        "### Evaluator Strategy Hint\n"
        f"{eval_hint if eval_hint else 'No strategy hint yet.'}\n\n"
        "### Last Evaluation JSON\n"
        f"```json\n{json.dumps(last_eval, indent=2)}\n```"
    )


# ---------------------------------------------------------
# AUTH FLOW
# ---------------------------------------------------------
def handle_signup(name, email, password):
    """
    Signup handler.
    """
    ok, message = signup_user(name=name, email=email, password=password)
    return message


def handle_login(email, password):
    """
    Login handler.

    Expected login_user return:
        success, message, user
    where user is something like:
        {"id": "...", "name": "...", "email": "..."}
    """
    success, message, user = login_user(email=email, password=password)

    if not success:
        return (
            False,                 # logged_in
            None,                  # user_state
            "Login failed",        # status
            "",                    # profile markdown
            message                # auth message
        )

    profile = load_profile(user["id"])
    profile = ensure_profile_structure(profile)
    profile["sessions"] += 1
    save_profile(user["id"], profile)

    return (
        True,
        user,
        f"Logged in as {user['name']}",
        profile_to_markdown(profile),
        "Login successful"
    )


def handle_logout():
    """
    Logout handler.
    """
    return (
        False,     # logged_in
        None,      # user_state
        "Logged out",
        "",        # profile markdown
        "You have been logged out."
    )


# ---------------------------------------------------------
# QUESTION FLOW
# ---------------------------------------------------------
def handle_question(user_state, chat_history, user_question):
    """
    Handle main tutor question.

    user_state: current logged-in user dict
    chat_history: current chatbot history
    user_question: learner input

    Returns:
    chatbot_history,
    followup_context,
    detected_level,
    confidence_text,
    detected_topic,
    tutor_answer,
    followup_question,
    examples_markdown,
    profile_markdown,
    evaluation_markdown,
    status_message
    """
    if chat_history is None:
        chat_history = []

    if not user_state:
        return (
            chat_history,
            None,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "Please login first."
        )

    if not user_question or not user_question.strip():
        return (
            chat_history,
            None,
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "Please enter a question."
        )

    user_id = user_state["id"]
    profile = load_profile(user_id)
    profile = ensure_profile_structure(profile)

    # Tutor Agent
    level, confidence, topic, examples, answer = generate_tutor_response(user_question, profile)

    # Memory update after question
    profile = update_profile_after_question(profile, topic, level)
    save_profile(user_id, profile)

    # Evaluator Agent: generate follow-up
    followup_question = generate_followup_question(
        user_question=user_question,
        tutor_answer=answer,
        level=level,
        topic=topic
    )

    bot_reply = (
        f"**Answer:**\n{answer}\n\n"
        f"**Check your understanding:**\n{followup_question}"
    )

    chat_history = chat_history + [
        {"role": "user", "content": user_question},
        {"role": "assistant", "content": bot_reply},
    ]

    # Store context needed when learner replies to follow-up
    followup_context = {
        "topic": topic,
        "level": level,
        "followup_question": followup_question,
        "last_user_question": user_question,
        "last_tutor_answer": answer,
    }

    return (
        chat_history,
        followup_context,
        level,
        confidence_to_text(confidence),
        topic,
        answer,
        followup_question,
        examples_to_markdown(examples),
        profile_to_markdown(profile),
        "",
        "Question answered successfully."
    )


# ---------------------------------------------------------
# FOLLOW-UP EVALUATION FLOW
# ---------------------------------------------------------
def handle_followup_reply(user_state, followup_context, learner_reply):
    if not user_state:
        return "", "", "Please login first."

    if not followup_context:
        return "", "", "No follow-up question found yet. Ask a main question first."

    if not learner_reply or not learner_reply.strip():
        return "", "", "Please enter your reply to the follow-up question."

    user_id = user_state["id"]
    profile = load_profile(user_id)
    profile = ensure_profile_structure(profile)

    topic = followup_context["topic"]
    level = followup_context["level"]
    followup_question = followup_context["followup_question"]

    evaluation = evaluate_followup_response(
        topic=topic,
        level=level,
        followup_question=followup_question,
        learner_reply=learner_reply
    )

    profile = update_profile_after_evaluation(profile, topic, evaluation)
    profile = update_last_evaluation(profile, topic, evaluation)
    save_profile(user_id, profile)

    return (
        format_evaluation_markdown(evaluation),
        profile_to_markdown(profile),
        "Follow-up evaluated successfully."
    )
# ---------------------------------------------------------
# SESSION / RESET HELPERS
# ---------------------------------------------------------
def clear_chat_and_followup(user_state):
    """
    Clear only the visible chat and follow-up context.
    Keep user profile persisted.
    """
    profile_md = ""
    if user_state:
        profile = load_profile(user_state["id"])
        profile = ensure_profile_structure(profile)
        profile_md = profile_to_markdown(profile)

    return (
        [],        # chat_history
        None,      # followup_context
        "", "", "", "", "", "",  # detected level / conf / topic / answer / followup / examples
        profile_md,
        "",        # evaluation markdown
        "Chat cleared."
    )


# ---------------------------------------------------------
# APP CREATION
# ---------------------------------------------------------
def create_app():
    """
    Create the Gradio application.
    """
    init_db()

    # Legacy UI compatibility wrappers: preserve the previous layout/flow.
    def handle_signup_legacy(name, username, email, password):
        ok, message = signup_user(name=name, email=email, password=password, username=username)
        if ok:
            return message, "", "", "", ""
        return message, name, username, email, ""

    def handle_login_legacy(identifier, password):
        success, message, user = login_user(email=identifier, password=password)
        if not success:
            return (
                message,
                None,
                "",
                [],
                [],
                "",
                "",
                "",
                "",
                "",
                _placeholder_chart("Mastery by Topic", "Login to view mastery trends."),
                _placeholder_chart("Topic Revisit Count", "Login to view topic revisits."),
                _placeholder_chart("Weak Concept Count by Topic", "Login to view weak concepts."),
                gr.update(visible=True),
                gr.update(visible=False),
            )
        profile = load_profile(user["id"])
        profile = ensure_profile_structure(profile)
        profile["sessions"] += 1
        save_profile(user["id"], profile)
        insights_md = build_system_insights_markdown(profile=profile)
        return (
            message,
            user,
            f"Logged in as **{user['name']}** ({user['email']})",
            [],
            [],
            "",
            "",
            "",
            profile_to_markdown(profile),
            insights_md,
            build_mastery_chart(profile),
            build_topic_revisit_chart(profile),
            build_weak_concepts_chart(profile),
            gr.update(visible=False),
            gr.update(visible=True),
        )

    def handle_logout_legacy():
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
            "",
            _placeholder_chart("Mastery by Topic", "Login to view mastery trends."),
            _placeholder_chart("Topic Revisit Count", "Login to view topic revisits."),
            _placeholder_chart("Weak Concept Count by Topic", "Login to view weak concepts."),
            gr.update(visible=True),
            gr.update(visible=False),
        )

    def ask_eduagent_legacy(user_question, chat_history, user):
        (
            chatbot_history,
            followup_context,
            level,
            confidence_text,
            topic,
            _tutor_answer,
            followup_question,
            examples_markdown,
            profile_markdown,
            _evaluation_markdown,
            status_message,
        ) = handle_question(user, chat_history, user_question)
        if status_message in ("Please login first.", "Please enter a question."):
            profile_obj = ensure_profile_structure({})
            return (
                chatbot_history,
                chatbot_history,
                None,
                status_message,
                "",
                "",
                "",
                profile_markdown,
                examples_markdown,
                build_system_insights_markdown(profile=profile_obj),
                build_mastery_chart(profile_obj),
                build_topic_revisit_chart(profile_obj),
                build_weak_concepts_chart(profile_obj),
            )
        profile_obj = ensure_profile_structure(load_profile(user["id"]))
        return (
            chatbot_history,
            chatbot_history,
            followup_context,
            level,
            confidence_text,
            topic,
            followup_question,
            profile_markdown,
            examples_markdown,
            build_system_insights_markdown(level, confidence_text, topic, profile_obj),
            build_mastery_chart(profile_obj),
            build_topic_revisit_chart(profile_obj),
            build_weak_concepts_chart(profile_obj),
        )

    def clear_chat_legacy(user_state=None):
        if user_state:
            profile_obj = ensure_profile_structure(load_profile(user_state["id"]))
            profile_markdown = profile_to_markdown(profile_obj)
        else:
            profile_obj = ensure_profile_structure({})
            profile_markdown = ""
        return (
            [],
            [],
            None,
            "",
            "",
            "",
            "",
            profile_markdown,
            "",
            "",
            build_system_insights_markdown(profile=profile_obj),
            build_mastery_chart(profile_obj),
            build_topic_revisit_chart(profile_obj),
            build_weak_concepts_chart(profile_obj),
        )

    def handle_followup_reply_legacy(user_state, followup_context, learner_reply):
        evaluation_md, updated_profile_md, status_message = handle_followup_reply(
            user_state, followup_context, learner_reply
        )
        profile_obj = ensure_profile_structure(load_profile(user_state["id"])) if user_state else ensure_profile_structure({})
        topic = followup_context.get("topic", "") if followup_context else ""
        level = followup_context.get("level", "") if followup_context else ""
        return (
            evaluation_md,
            updated_profile_md,
            status_message,
            build_system_insights_markdown(level=level, topic=topic, profile=profile_obj),
            build_mastery_chart(profile_obj),
            build_topic_revisit_chart(profile_obj),
            build_weak_concepts_chart(profile_obj),
        )

    return build_demo(
        handle_signup=handle_signup_legacy,
        handle_login=handle_login_legacy,
        handle_logout=handle_logout_legacy,
        ask_eduagent=ask_eduagent_legacy,
        clear_chat=clear_chat_legacy,
        handle_followup_reply=handle_followup_reply_legacy,
    )

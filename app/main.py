import json
import gradio as gr

from auth.auth_service import signup_user, login_user
from db.profile_repository import load_profile, save_profile
from agents.tutor_agent import generate_tutor_response
from agents.evaluator_agent import (
    generate_followup_question,
    evaluate_followup_response,
)
from agents.memory_agent import (
    ensure_profile_structure,
    update_profile_after_question,
    update_profile_after_evaluation,
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

    weak_areas_lines = []
    for topic, concepts in profile.get("weak_areas", {}).items():
        if concepts:
            weak_areas_lines.append(f"- **{topic}**: {', '.join(concepts)}")

    mastery_lines = []
    for topic, score in profile.get("mastery", {}).items():
        mastery_lines.append(f"- **{topic}**: {score}")

    recommendations = profile.get("recommended_next_topics", [])

    return (
        f"**Sessions:** {profile.get('sessions', 0)}\n\n"
        f"**Questions Asked:** {profile.get('questions_asked', 0)}\n\n"
        f"**Last Level:** {profile.get('last_level', 'beginner')}\n\n"
        f"**Topics Seen:** {', '.join(profile.get('topics_seen', [])) if profile.get('topics_seen') else 'None'}\n\n"
        f"**Weak Areas:**\n"
        f"{chr(10).join(weak_areas_lines) if weak_areas_lines else 'None'}\n\n"
        f"**Mastery:**\n"
        f"{chr(10).join(mastery_lines) if mastery_lines else 'None'}\n\n"
        f"**Recommended Next Topics:** {', '.join(recommendations) if recommendations else 'None'}"
    )


def format_evaluation_markdown(evaluation: dict):
    return (
        f"**Understanding Level:** {evaluation.get('understanding_level', 'partial')}\n\n"
        f"**Weak Concepts:** {', '.join(evaluation.get('weak_concepts', [])) if evaluation.get('weak_concepts') else 'None'}\n\n"
        f"**Feedback:** {evaluation.get('feedback', '')}\n\n"
        f"**Recommended Action:** {evaluation.get('recommended_action', '')}"
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
    """
    Handle learner reply to evaluator follow-up question.

    Returns:
    evaluation_markdown,
    updated_profile_markdown,
    status_message
    """
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
    # Legacy UI compatibility wrappers: preserve the previous layout/flow.
    def handle_signup_legacy(name, username, email, password):
        _ = username  # legacy field retained in UI; not required by current auth service
        return handle_signup(name, email, password), "", "", "", ""

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
                gr.update(visible=True),
                gr.update(visible=False),
            )
        profile = load_profile(user["id"])
        profile = ensure_profile_structure(profile)
        profile["sessions"] += 1
        save_profile(user["id"], profile)
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
            return chatbot_history, chatbot_history, None, status_message, "", "", "", profile_markdown, examples_markdown
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
        )

    def clear_chat_legacy():
        return [], [], None, "", "", "", "", "", ""

    def handle_followup_reply_legacy(user_state, followup_context, learner_reply):
        evaluation_md, updated_profile_md, status_message = handle_followup_reply(
            user_state, followup_context, learner_reply
        )
        return evaluation_md, updated_profile_md, status_message

    return build_demo(
        handle_signup=handle_signup_legacy,
        handle_login=handle_login_legacy,
        handle_logout=handle_logout_legacy,
        ask_eduagent=ask_eduagent_legacy,
        clear_chat=clear_chat_legacy,
        handle_followup_reply=handle_followup_reply_legacy,
    )
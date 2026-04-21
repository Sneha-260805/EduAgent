import gradio as gr
from auth.auth_service import register_user, authenticate_user
from db.sqlite_store import init_db
from db.profile_repository import load_profile, save_profile
from agents.tutor_agent import generate_tutor_response, examples_to_markdown
from agents.evaluator_agent import generate_followup_question
from agents.memory_agent import update_learning_signals, build_memory_hint
from ml.classifier import predict_level
from ml.topic_detector import detect_best_topic
from ml.retriever import df
from app.ui import build_demo


def profile_to_markdown(profile):
    recent_q = profile.get("question_history", [])[-3:]
    recent_text = "\n".join([f"- {q['question']}" for q in reversed(recent_q)]) if recent_q else "None"
    return (
        f"**Sessions:** {profile['sessions']}\n\n"
        f"**Questions Asked:** {profile['questions_asked']}\n\n"
        f"**Last Level:** {profile['last_level']}\n\n"
        f"**Topics Seen:** {', '.join(profile['topics_seen']) if profile['topics_seen'] else 'None'}\n\n"
        f"**Weak Areas:** {', '.join(profile['weak_areas']) if profile['weak_areas'] else 'None'}\n\n"
        f"**Recommended Next Topics:** {', '.join(profile['recommended_next_topics']) if profile['recommended_next_topics'] else 'None'}\n\n"
        f"**Recent Questions:**\n{recent_text}"
    )


def confidence_to_text(conf):
    return (
        f"Beginner: {conf[0]:.3f} | "
        f"Intermediate: {conf[1]:.3f} | "
        f"Advanced: {conf[2]:.3f}"
    )


def user_welcome(user):
    if not user:
        return "Not logged in."
    return f"Logged in as **{user['name']}** ({user['email']})"


def handle_signup(name, username, email, password):
    ok, msg = register_user(name, username, email, password)
    if ok:
        return msg, "", "", "", ""
    return msg, name, username, email, ""


def handle_login(identifier, password):
    user, msg = authenticate_user(identifier, password)
    if not user:
        return (
            msg,
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

    profile = load_profile(user["user_id"])
    profile["sessions"] += 1
    save_profile(user["user_id"], profile)
    return (
        msg,
        user,
        user_welcome(user),
        [],
        [],
        "",
        "",
        "",
        profile_to_markdown(profile),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def handle_logout():
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


def ask_eduagent(user_question, chat_history, user):
    if chat_history is None:
        chat_history = []
    if not user:
        return chat_history, chat_history, "Please login first.", "", "", "", "", ""

    if not user_question or not user_question.strip():
        profile = load_profile(user["user_id"])
        return chat_history, chat_history, "Please enter a question.", "", "", "", profile_to_markdown(profile), ""

    profile = load_profile(user["user_id"])
    estimated_level, _ = predict_level(user_question)
    estimated_topic = detect_best_topic(user_question, estimated_level, df)
    memory_hint = build_memory_hint(profile, estimated_topic)
    level, confidence, topic, examples, answer = generate_tutor_response(user_question, memory_hint=memory_hint)
    followup = generate_followup_question(user_question, answer, level)

    profile = update_learning_signals(profile, user_question, level, topic)
    save_profile(user["user_id"], profile)

    bot_reply = f"**Answer:**\n{answer}\n\n**Check your understanding:**\n{followup}"
    chat_history = chat_history + [
        {"role": "user", "content": user_question},
        {"role": "assistant", "content": bot_reply},
    ]

    return (
        chat_history,
        chat_history,
        level,
        confidence_to_text(confidence),
        topic,
        followup,
        profile_to_markdown(profile),
        examples_to_markdown(examples),
    )


def clear_chat():
    return [], [], "", "", "", "", "", ""


def create_app():
    init_db()
    return build_demo(
        handle_signup=handle_signup,
        handle_login=handle_login,
        handle_logout=handle_logout,
        ask_eduagent=ask_eduagent,
        clear_chat=clear_chat,
    )


if __name__ == "__main__":
    demo = create_app()
    demo.launch()

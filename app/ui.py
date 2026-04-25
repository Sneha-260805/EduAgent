import gradio as gr


CUSTOM_CSS = """
:root {
    color-scheme: dark;
}
body {
    background:
        radial-gradient(circle at top left, rgba(20, 184, 166, 0.16), transparent 32rem),
        radial-gradient(circle at 82% 18%, rgba(59, 130, 246, 0.14), transparent 28rem),
        #060913 !important;
}
.gradio-container {
    max-width: 1560px !important;
    padding: 22px 24px 32px !important;
    background: transparent !important;
    color: #e5e7eb;
    --body-background-fill: #060913;
    --background-fill-primary: #0b1120;
    --background-fill-secondary: #101827;
    --block-background-fill: #0f172a;
    --block-border-color: rgba(148, 163, 184, 0.22);
    --block-info-text-color: #94a3b8;
    --body-text-color: #e5e7eb;
    --body-text-color-subdued: #94a3b8;
    --input-background-fill: rgba(15, 23, 42, 0.94);
    --input-border-color: rgba(148, 163, 184, 0.26);
    --button-primary-background-fill: linear-gradient(135deg, #14b8a6, #2563eb);
    --button-primary-background-fill-hover: linear-gradient(135deg, #2dd4bf, #3b82f6);
    --button-primary-text-color: #ffffff;
    --button-secondary-background-fill: rgba(30, 41, 59, 0.92);
    --button-secondary-background-fill-hover: rgba(51, 65, 85, 0.96);
    --button-secondary-text-color: #e2e8f0;
    --border-color-primary: rgba(148, 163, 184, 0.22);
    --border-color-accent: rgba(20, 184, 166, 0.55);
}
.main-title {
    text-align: center;
    font-size: 38px;
    line-height: 1.05;
    font-weight: 900;
    color: #f8fafc;
    margin-bottom: 8px;
    letter-spacing: 0;
}
.sub-title {
    text-align: center;
    font-size: 15px;
    color: #9ca3af;
    margin-bottom: 24px;
}
.auth-shell {
    max-width: 1180px;
    margin: 0 auto;
    align-items: stretch;
}
.auth-hero {
    min-height: 520px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    padding: 30px;
    background:
        linear-gradient(145deg, rgba(20, 184, 166, 0.18), rgba(37, 99, 235, 0.10)),
        linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.96));
    box-shadow: 0 24px 70px rgba(2, 6, 23, 0.38);
}
.auth-kicker {
    color: #5eead4;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    margin-bottom: 18px;
}
.auth-headline {
    color: #f8fafc;
    font-size: 42px;
    line-height: 1.05;
    font-weight: 900;
    margin-bottom: 16px;
    letter-spacing: 0;
}
.auth-copy {
    color: #cbd5e1;
    font-size: 15px;
    line-height: 1.65;
    max-width: 560px;
}
.auth-metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 26px 0;
}
.auth-metric {
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    padding: 13px 14px;
    background: rgba(15, 23, 42, 0.72);
}
.auth-metric strong {
    display: block;
    color: #f8fafc;
    font-size: 20px;
}
.auth-metric span {
    color: #94a3b8;
    font-size: 12px;
}
.auth-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}
.auth-pill {
    border: 1px solid rgba(94, 234, 212, 0.28);
    border-radius: 999px;
    color: #ccfbf1;
    background: rgba(13, 148, 136, 0.12);
    padding: 8px 11px;
    font-size: 12px;
    font-weight: 700;
}
.auth-card {
    border: 1px solid rgba(148, 163, 184, 0.24);
    border-radius: 8px;
    padding: 20px;
    min-height: 520px;
    background: rgba(15, 23, 42, 0.90);
    box-shadow: 0 24px 70px rgba(2, 6, 23, 0.34);
    backdrop-filter: blur(16px);
}
.auth-card::before {
    content: "Secure learner workspace";
    display: block;
    color: #e2e8f0;
    font-weight: 800;
    font-size: 20px;
    margin-bottom: 4px;
}
.auth-card::after {
    content: "Sign in to continue your tutoring session or create a new learner profile.";
    display: block;
    color: #94a3b8;
    font-size: 13px;
    margin-bottom: 18px;
}
.auth-status {
    max-width: 1180px;
    margin: 0 auto 12px;
}
.topbar {
    align-items: center;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.86);
    padding: 12px 14px;
    margin-bottom: 16px;
    box-shadow: 0 18px 48px rgba(2, 6, 23, 0.28);
}
.welcome-text {
    color: #e2e8f0;
    font-weight: 700;
}
.chat-panel,
.dashboard-card {
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 8px;
    background:
        linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(10, 17, 31, 0.96));
    padding: 16px;
    box-shadow: 0 18px 54px rgba(2, 6, 23, 0.30);
}
.dashboard-card {
    margin-bottom: 14px;
}
.dashboard-shell {
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 8px;
    background:
        linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(8, 13, 25, 0.96));
    padding: 14px;
    box-shadow: 0 18px 54px rgba(2, 6, 23, 0.30);
}
.dashboard-heading {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 2px 2px 12px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.14);
    margin-bottom: 12px;
}
.dashboard-eyebrow {
    color: #5eead4;
    font-size: 11px;
    font-weight: 850;
    text-transform: uppercase;
}
.dashboard-name {
    color: #f8fafc;
    font-size: 20px;
    font-weight: 900;
    margin-top: 2px;
}
.dashboard-note {
    color: #94a3b8;
    font-size: 12px;
    max-width: 280px;
}
.dashboard-tabs {
    background: transparent !important;
}
.dashboard-tabs > .tab-nav,
.chart-tabs > .tab-nav {
    gap: 6px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.16) !important;
    padding-bottom: 8px;
    margin-bottom: 12px;
}
.dashboard-tabs > .tab-nav button,
.chart-tabs > .tab-nav button {
    border: 1px solid rgba(148, 163, 184, 0.18) !important;
    border-radius: 8px !important;
    background: rgba(2, 6, 23, 0.34) !important;
    padding: 8px 10px !important;
}
.dashboard-tabs > .tab-nav button.selected,
.chart-tabs > .tab-nav button.selected {
    background: rgba(20, 184, 166, 0.14) !important;
    border-color: rgba(94, 234, 212, 0.42) !important;
}
.compact-card {
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    background: rgba(2, 6, 23, 0.24);
    padding: 14px;
    margin-bottom: 12px;
}
.chart-panel {
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 8px;
    background: rgba(2, 6, 23, 0.24);
    padding: 10px;
    margin-bottom: 10px;
}
.scroll-panel {
    max-height: 390px;
    overflow-y: auto;
    padding-right: 8px;
}
.research-panel {
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 8px;
    background: rgba(2, 6, 23, 0.24);
    padding: 12px;
}
.examples-panel {
    max-height: 440px;
}
.section-title {
    font-size: 17px;
    font-weight: 800;
    margin-bottom: 4px;
    color: #f8fafc;
}
.muted-caption {
    color: #94a3b8;
    font-size: 12px;
    margin-bottom: 12px;
}
.gr-button-primary,
button {
    border-radius: 8px !important;
    font-weight: 750 !important;
    border-color: rgba(148, 163, 184, 0.22) !important;
}
textarea,
input {
    border-radius: 8px !important;
    color: #e5e7eb !important;
    background: rgba(2, 6, 23, 0.54) !important;
    border-color: rgba(148, 163, 184, 0.26) !important;
}
label,
.label-wrap,
.gradio-container span,
.gradio-container p,
.gradio-container li {
    color: #cbd5e1;
}
.prose,
.markdown,
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4 {
    color: #f8fafc;
}
.gradio-container [data-testid="block-label"] {
    color: #9ca3af !important;
    background: rgba(15, 23, 42, 0.92) !important;
}
.gradio-container .tabs,
.gradio-container .tabitem,
.gradio-container .tab-nav {
    background: transparent !important;
}
.gradio-container .tab-nav button {
    color: #cbd5e1 !important;
}
.gradio-container .tab-nav button.selected {
    color: #5eead4 !important;
    border-color: #14b8a6 !important;
}
.gradio-container .wrap,
.gradio-container .block,
.gradio-container .form,
.gradio-container .panel {
    background: rgba(15, 23, 42, 0.78) !important;
    border-color: rgba(148, 163, 184, 0.20) !important;
}
.chatbot {
    background:
        linear-gradient(180deg, rgba(2, 6, 23, 0.72), rgba(15, 23, 42, 0.88)) !important;
    border-color: rgba(148, 163, 184, 0.20) !important;
}
.eval-card {
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-left: 5px solid #64748b;
    border-radius: 8px;
    padding: 13px 14px;
    background: rgba(15, 23, 42, 0.82);
}
.eval-good {
    border-left-color: #22c55e;
    background: rgba(22, 101, 52, 0.22);
}
.eval-partial {
    border-left-color: #f59e0b;
    background: rgba(146, 64, 14, 0.22);
}
.eval-poor {
    border-left-color: #ef4444;
    background: rgba(127, 29, 29, 0.26);
}
.profile-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}
.profile-card {
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    padding: 12px 13px;
    background: rgba(2, 6, 23, 0.34);
}
.profile-card h4 {
    margin: 0 0 6px;
    color: #67e8f9;
    font-size: 13px;
}
.profile-card p,
.profile-card li {
    color: #cbd5e1;
    font-size: 13px;
}
.profile-card ul {
    margin: 0;
    padding-left: 18px;
}
.wide-card {
    grid-column: 1 / -1;
}
.insight-block {
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 8px;
    background: rgba(2, 6, 23, 0.34);
    padding: 12px 13px;
    margin-bottom: 10px;
}
.insight-block h4 {
    margin: 0 0 6px;
    color: #67e8f9;
    font-size: 13px;
}
code,
pre {
    background: #020617 !important;
    color: #d1fae5 !important;
    border-color: rgba(148, 163, 184, 0.18) !important;
}
@media (max-width: 900px) {
    .auth-hero {
        min-height: auto;
    }
    .auth-metrics {
        grid-template-columns: 1fr;
    }
    .profile-grid {
        grid-template-columns: 1fr;
    }
}
"""


def build_demo(
    handle_signup,
    handle_login,
    handle_logout,
    ask_eduagent,
    clear_chat,
    handle_followup_reply=None,
):
    with gr.Blocks() as demo:
        gr.HTML(
            """
            <div class="main-title">EduAgent - Adaptive AI Tutor</div>
            <div class="sub-title">Learner-aware tutoring with difficulty detection, topic retrieval, memory, and comprehension checking</div>
            """
        )
        auth_status = gr.Markdown("", elem_classes=["auth-status"])
        user_state = gr.State(None)
        state = gr.State([])
        followup_context_state = gr.State(None)

        with gr.Column(visible=True, elem_classes=["auth-section"]) as auth_section:
            with gr.Row(elem_classes=["auth-shell"]):
                with gr.Column(scale=6, min_width=430):
                    gr.HTML(
                        """
                        <div class="auth-hero">
                            <div class="auth-kicker">Academic showcase dashboard</div>
                            <div class="auth-headline">Adaptive AI tutoring with visible learning intelligence.</div>
                            <div class="auth-copy">
                                EduAgent combines a tutor, evaluator, memory agent, difficulty classifier, and retrieval pipeline into one polished learner workspace.
                            </div>
                            <div class="auth-metrics">
                                <div class="auth-metric"><strong>Live</strong><span>difficulty signals</span></div>
                                <div class="auth-metric"><strong>Memory</strong><span>profile updates</span></div>
                                <div class="auth-metric"><strong>Charts</strong><span>mastery tracking</span></div>
                            </div>
                            <div class="auth-pills">
                                <span class="auth-pill">Tutor Agent</span>
                                <span class="auth-pill">Evaluator Agent</span>
                                <span class="auth-pill">Memory Agent</span>
                                <span class="auth-pill">System Insights</span>
                            </div>
                        </div>
                        """
                    )
                with gr.Column(scale=4, min_width=360):
                    with gr.Group(elem_classes=["auth-card"]):
                        with gr.Tab("Login"):
                            login_identifier = gr.Textbox(label="Email or Username")
                            login_password = gr.Textbox(label="Password", type="password")
                            login_btn = gr.Button("Login", variant="primary")

                        with gr.Tab("Signup"):
                            signup_name = gr.Textbox(label="Full Name")
                            signup_username = gr.Textbox(label="Username (optional)")
                            signup_email = gr.Textbox(label="Email")
                            signup_password = gr.Textbox(label="Password (min 6 chars)", type="password")
                            signup_btn = gr.Button("Create Account")

        with gr.Column(visible=False, elem_classes=["app-section"]) as app_section:
            with gr.Row(elem_classes=["topbar"]):
                with gr.Column(scale=8):
                    welcome_md = gr.Markdown("", elem_classes=["welcome-text"])
                with gr.Column(scale=1, min_width=120):
                    logout_btn = gr.Button("Logout")

            with gr.Row():
                with gr.Column(scale=7, min_width=520):
                    with gr.Group(elem_classes=["chat-panel"]):
                        gr.HTML(
                            """
                            <div class='section-title'>Tutor Conversation</div>
                            <div class='muted-caption'>Ask a question, review the explanation, then answer the follow-up check.</div>
                            """
                        )
                        chatbot = gr.Chatbot(label="Conversation", height=590)
                        user_input = gr.Textbox(
                            label="Ask your AI/ML question",
                            placeholder="Example: What is reinforcement learning?",
                            lines=3,
                        )
                        with gr.Row():
                            ask_btn = gr.Button("Ask EduAgent", variant="primary")
                            clear_btn = gr.Button("Clear Chat")

                with gr.Column(scale=5, min_width=460):
                    with gr.Group(elem_classes=["dashboard-shell"]):
                        gr.HTML(
                            """
                            <div class='dashboard-heading'>
                                <div>
                                    <div class='dashboard-eyebrow'>Learner Workspace</div>
                                    <div class='dashboard-name'>Dashboard</div>
                                </div>
                                <div class='dashboard-note'>Core learner state first. Research details stay available without crowding the tutoring flow.</div>
                            </div>
                            """
                        )

                        with gr.Tabs(elem_classes=["dashboard-tabs"]):
                            with gr.Tab("Overview"):
                                with gr.Group(elem_classes=["compact-card"]):
                                    gr.HTML(
                                        """
                                        <div class='section-title'>Learner Snapshot</div>
                                        <div class='muted-caption'>Live signals from classification and topic detection.</div>
                                        """
                                    )
                                    with gr.Row():
                                        level_box = gr.Textbox(label="Detected Level", interactive=False)
                                        topic_box = gr.Textbox(label="Detected Topic", interactive=False)
                                    conf_box = gr.Textbox(label="Confidence Scores", interactive=False)

                                with gr.Group(elem_classes=["compact-card"]):
                                    gr.HTML(
                                        """
                                        <div class='section-title'>Learner Memory / Progress</div>
                                        <div class='muted-caption'>Persisted learner state summarized for presentation.</div>
                                        """
                                    )
                                    profile_md = gr.Markdown("No profile data yet.", elem_classes=["scroll-panel"])

                            with gr.Tab("Evaluate"):
                                with gr.Group(elem_classes=["compact-card"]):
                                    gr.HTML(
                                        """
                                        <div class='section-title'>Follow-up Evaluation</div>
                                        <div class='muted-caption'>Answer the comprehension check to update mastery and weak areas.</div>
                                        """
                                    )
                                    followup_box = gr.Textbox(label="Check Your Understanding", lines=3, interactive=False)
                                    followup_reply = gr.Textbox(
                                        label="Your Follow-up Answer",
                                        placeholder="Write your answer to the follow-up question here...",
                                        lines=4,
                                    )
                                    eval_btn = gr.Button("Evaluate Follow-up", variant="secondary")
                                    evaluation_md = gr.Markdown("No evaluation yet.")
                                    eval_status = gr.Markdown("")

                            with gr.Tab("Progress"):
                                gr.HTML(
                                    """
                                    <div class='section-title'>Charts</div>
                                    <div class='muted-caption'>Progress visuals update after questions and follow-up evaluation.</div>
                                    """
                                )
                                with gr.Tabs(elem_classes=["chart-tabs"]):
                                    with gr.Tab("Mastery"):
                                        with gr.Group(elem_classes=["chart-panel"]):
                                            mastery_plot = gr.Plot(label="Mastery by Topic")
                                    with gr.Tab("Revisits"):
                                        with gr.Group(elem_classes=["chart-panel"]):
                                            revisit_plot = gr.Plot(label="Topic Revisit Count")
                                    with gr.Tab("Weak Areas"):
                                        with gr.Group(elem_classes=["chart-panel"]):
                                            weak_concept_plot = gr.Plot(label="Weak Concept Count by Topic")

                            with gr.Tab("Research"):
                                with gr.Group(elem_classes=["research-panel"]):
                                    with gr.Accordion("System Insights / Admin Panel", open=True):
                                        insights_md = gr.Markdown("No system insights yet.", elem_classes=["scroll-panel"])
                                    with gr.Accordion("Retrieved Examples", open=False):
                                        examples_md = gr.Markdown(
                                            "No examples yet.",
                                            elem_classes=["scroll-panel", "examples-panel"],
                                        )

        signup_btn.click(
            fn=handle_signup,
            inputs=[signup_name, signup_username, signup_email, signup_password],
            outputs=[auth_status, signup_name, signup_username, signup_email, signup_password],
        )

        login_btn.click(
            fn=handle_login,
            inputs=[login_identifier, login_password],
            outputs=[
                auth_status, user_state, welcome_md, chatbot, state, level_box, conf_box, topic_box,
                profile_md, insights_md, mastery_plot, revisit_plot, weak_concept_plot, auth_section, app_section,
            ],
        ).then(fn=lambda: ("", ""), inputs=None, outputs=[login_identifier, login_password])

        logout_btn.click(
            fn=handle_logout,
            inputs=None,
            outputs=[
                auth_status, user_state, welcome_md, chatbot, state, level_box, conf_box, topic_box,
                profile_md, insights_md, mastery_plot, revisit_plot, weak_concept_plot, auth_section, app_section,
            ],
        )

        ask_btn.click(
            fn=ask_eduagent,
            inputs=[user_input, state, user_state],
            outputs=[
                chatbot, state, followup_context_state, level_box, conf_box, topic_box, followup_box,
                profile_md, examples_md, insights_md, mastery_plot, revisit_plot, weak_concept_plot,
            ],
        ).then(fn=lambda: "", inputs=None, outputs=[user_input])

        user_input.submit(
            fn=ask_eduagent,
            inputs=[user_input, state, user_state],
            outputs=[
                chatbot, state, followup_context_state, level_box, conf_box, topic_box, followup_box,
                profile_md, examples_md, insights_md, mastery_plot, revisit_plot, weak_concept_plot,
            ],
        ).then(fn=lambda: "", inputs=None, outputs=[user_input])

        if handle_followup_reply is not None:
            eval_btn.click(
                fn=handle_followup_reply,
                inputs=[user_state, followup_context_state, followup_reply],
                outputs=[evaluation_md, profile_md, eval_status, insights_md, mastery_plot, revisit_plot, weak_concept_plot],
            ).then(fn=lambda: "", inputs=None, outputs=[followup_reply])

        clear_btn.click(
            fn=clear_chat,
            inputs=[user_state],
            outputs=[
                chatbot, state, followup_context_state, level_box, conf_box, topic_box, followup_box,
                profile_md, examples_md, insights_md, mastery_plot, revisit_plot, weak_concept_plot,
            ],
        ).then(fn=lambda: ("", "", "No evaluation yet."), inputs=None, outputs=[followup_reply, eval_status, evaluation_md])
    return demo


def build_ui(
    handle_signup,
    handle_login,
    handle_logout,
    handle_question,
    handle_followup_reply,
    clear_chat_and_followup,
):
    """
    UI builder expected by app.main handlers.
    """
    with gr.Blocks() as demo:
        gr.HTML(
            """
            <div class="main-title">EduAgent - Adaptive AI Tutor</div>
            <div class="sub-title">Learner-aware tutoring with difficulty detection, retrieval, and follow-up evaluation</div>
            """
        )
        auth_status = gr.Markdown("")
        user_state = gr.State(None)
        logged_in = gr.State(False)
        chat_state = gr.State([])
        followup_context = gr.State(None)

        with gr.Column(visible=True) as auth_section:
            signup_name = gr.Textbox(label="Full Name")
            signup_email = gr.Textbox(label="Email")
            signup_password = gr.Textbox(label="Password", type="password")
            signup_btn = gr.Button("Create Account")

            login_email = gr.Textbox(label="Login Email")
            login_password = gr.Textbox(label="Login Password", type="password")
            login_btn = gr.Button("Login", variant="primary")

        with gr.Column(visible=False) as app_section:
            welcome_md = gr.Markdown("")
            logout_btn = gr.Button("Logout")

            chatbot = gr.Chatbot(label="Tutor Conversation", height=420)
            user_input = gr.Textbox(label="Ask your AI/ML question", lines=3)
            ask_btn = gr.Button("Ask EduAgent", variant="primary")

            followup_reply = gr.Textbox(label="Reply to follow-up question", lines=3)
            eval_btn = gr.Button("Evaluate Reply")

            clear_btn = gr.Button("Clear Chat")

            level_box = gr.Textbox(label="Detected Level", interactive=False)
            conf_box = gr.Textbox(label="Confidence Scores", interactive=False)
            topic_box = gr.Textbox(label="Detected Topic", interactive=False)
            answer_box = gr.Textbox(label="Tutor Answer", lines=6, interactive=False)
            followup_box = gr.Textbox(label="Follow-up Question", lines=3, interactive=False)
            examples_md = gr.Markdown()
            profile_md = gr.Markdown()
            evaluation_md = gr.Markdown()
            status_box = gr.Markdown()

        signup_btn.click(
            fn=handle_signup,
            inputs=[signup_name, signup_email, signup_password],
            outputs=[auth_status],
        )

        login_btn.click(
            fn=handle_login,
            inputs=[login_email, login_password],
            outputs=[logged_in, user_state, welcome_md, profile_md, auth_status],
        ).then(
            fn=lambda is_logged_in: (gr.update(visible=not is_logged_in), gr.update(visible=is_logged_in)),
            inputs=[logged_in],
            outputs=[auth_section, app_section],
        )

        logout_btn.click(
            fn=handle_logout,
            inputs=None,
            outputs=[logged_in, user_state, welcome_md, profile_md, auth_status],
        ).then(
            fn=lambda: (gr.update(visible=True), gr.update(visible=False), [], None, "", "", "", "", "", "", ""),
            inputs=None,
            outputs=[auth_section, app_section, chatbot, followup_context, level_box, conf_box, topic_box, answer_box, followup_box, examples_md, evaluation_md],
        )

        ask_btn.click(
            fn=handle_question,
            inputs=[user_state, chat_state, user_input],
            outputs=[
                chatbot, followup_context, level_box, conf_box, topic_box, answer_box,
                followup_box, examples_md, profile_md, evaluation_md, status_box,
            ],
        ).then(
            fn=lambda chat: (chat, ""),
            inputs=[chatbot],
            outputs=[chat_state, user_input],
        )

        eval_btn.click(
            fn=handle_followup_reply,
            inputs=[user_state, followup_context, followup_reply],
            outputs=[evaluation_md, profile_md, status_box],
        ).then(
            fn=lambda: "",
            inputs=None,
            outputs=[followup_reply],
        )

        clear_btn.click(
            fn=clear_chat_and_followup,
            inputs=[user_state],
            outputs=[
                chatbot, followup_context, level_box, conf_box, topic_box, answer_box,
                followup_box, examples_md, profile_md, evaluation_md, status_box,
            ],
        ).then(
            fn=lambda chat: chat,
            inputs=[chatbot],
            outputs=[chat_state],
        )

    return demo

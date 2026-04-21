import gradio as gr


CUSTOM_CSS = """
.gradio-container {
    max-width: 1400px !important;
}
.main-title {
    text-align: center;
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 6px;
}
.sub-title {
    text-align: center;
    font-size: 16px;
    color: #888;
    margin-bottom: 18px;
}
"""


def build_demo(handle_signup, handle_login, handle_logout, ask_eduagent, clear_chat):
    with gr.Blocks(theme=gr.themes.Soft(), css=CUSTOM_CSS) as demo:
        gr.HTML(
            """
            <div class="main-title">EduAgent — Adaptive AI Tutor</div>
            <div class="sub-title">Learner-aware tutoring with difficulty detection, topic retrieval, memory, and comprehension checking</div>
            """
        )
        auth_status = gr.Markdown("")
        user_state = gr.State(None)
        state = gr.State([])

        with gr.Column(visible=True) as auth_section:
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

        with gr.Column(visible=False) as app_section:
            welcome_md = gr.Markdown("")
            logout_btn = gr.Button("Logout")

            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(label="Tutor Conversation", height=500)
                    user_input = gr.Textbox(
                        label="Ask your AI/ML question",
                        placeholder="Example: What is reinforcement learning?",
                        lines=3,
                    )
                    with gr.Row():
                        ask_btn = gr.Button("Ask EduAgent", variant="primary")
                        clear_btn = gr.Button("Clear Chat")

                with gr.Column(scale=2):
                    level_box = gr.Textbox(label="Detected Level", interactive=False)
                    conf_box = gr.Textbox(label="Confidence Scores", interactive=False)
                    topic_box = gr.Textbox(label="Detected Topic", interactive=False)
                    followup_box = gr.Textbox(label="Check Your Understanding", lines=4, interactive=False)
                    profile_md = gr.Markdown()
                    with gr.Accordion("Retrieved Examples", open=False):
                        examples_md = gr.Markdown()

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
                profile_md, auth_section, app_section,
            ],
        ).then(fn=lambda: ("", ""), inputs=None, outputs=[login_identifier, login_password])

        logout_btn.click(
            fn=handle_logout,
            inputs=None,
            outputs=[
                auth_status, user_state, welcome_md, chatbot, state, level_box, conf_box, topic_box,
                profile_md, auth_section, app_section,
            ],
        )

        ask_btn.click(
            fn=ask_eduagent,
            inputs=[user_input, state, user_state],
            outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md],
        ).then(fn=lambda: "", inputs=None, outputs=[user_input])

        user_input.submit(
            fn=ask_eduagent,
            inputs=[user_input, state, user_state],
            outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md],
        ).then(fn=lambda: "", inputs=None, outputs=[user_input])

        clear_btn.click(
            fn=clear_chat,
            inputs=None,
            outputs=[chatbot, state, level_box, conf_box, topic_box, followup_box, profile_md, examples_md],
        )
    return demo

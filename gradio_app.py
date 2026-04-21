import gradio as gr
from app.main import create_app


if __name__ == "__main__":
    demo = create_app()
    demo.launch(theme=gr.themes.Soft())

from groq import Groq
from config.settings import GROQ_API_KEY, MODEL_NAME
from ml.prompts import build_followup_prompt


client = Groq(api_key=GROQ_API_KEY)


def generate_followup_question(user_question, tutor_answer, level):
    prompt = build_followup_prompt(user_question, tutor_answer, level)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()

import os
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
DATASET_FILE = "eduagent_dataset.csv"
CLASSIFIER_PATH = "./difficulty_classifier"
DB_FILE = "eduagent.db"
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "2"))

CLASSIFIER_LABELS = ["beginner", "intermediate", "advanced"]

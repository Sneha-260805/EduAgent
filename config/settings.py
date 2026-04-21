import os
from dotenv import load_dotenv


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Set GROQ_API_KEY in your environment or .env file before running this app.")

MODEL_NAME = "llama-3.3-70b-versatile"
DATASET_FILE = "eduagent_dataset.csv"
CLASSIFIER_PATH = "./difficulty_classifier"
DB_FILE = "eduagent.db"

CLASSIFIER_LABELS = ["beginner", "intermediate", "advanced"]

import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from config.settings import CLASSIFIER_PATH, CLASSIFIER_LABELS


tokenizer = DistilBertTokenizer.from_pretrained(CLASSIFIER_PATH)
model = DistilBertForSequenceClassification.from_pretrained(CLASSIFIER_PATH)
model.eval()


def predict_level(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = F.softmax(logits, dim=1)
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]
    predicted_label = CLASSIFIER_LABELS[pred_idx]

    text_lower = text.lower().strip()

    if max(confidence) < 0.6:
        predicted_label = "intermediate"

    simple_patterns = [
        "what is",
        "how does",
        "explain",
        "flow of",
        "in simple terms",
    ]

    advanced_keywords = [
        "compare",
        "derive",
        "prove",
        "analyze",
        "convergence",
        "theorem",
        "optimization",
        "gradient clipping",
        "rmsprop",
        "adam",
        "backpropagation",
        "non-convex",
    ]

    has_simple_pattern = any(p in text_lower for p in simple_patterns)
    has_advanced_keyword = any(k in text_lower for k in advanced_keywords)

    if predicted_label == "advanced" and has_simple_pattern and not has_advanced_keyword:
        predicted_label = "intermediate"

    return predicted_label, confidence

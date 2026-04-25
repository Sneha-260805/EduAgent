import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from config.settings import CLASSIFIER_PATH, CLASSIFIER_LABELS


tokenizer = DistilBertTokenizer.from_pretrained(CLASSIFIER_PATH)
model = DistilBertForSequenceClassification.from_pretrained(CLASSIFIER_PATH)
model.eval()

LOW_CONFIDENCE_THRESHOLD = 0.6
ADVANCED_INTENT_MARKERS = (
    "analyze",
    "derive",
    "prove",
    "compare",
    "optimize",
    "convergence",
    "theorem",
    "architecture",
    "attention mechanism",
    "training objective",
    "scaling law",
    "fine tuning",
    "backpropagation",
)
BEGINNER_INTENT_PREFIXES = (
    "what is ",
    "what are ",
    "define ",
    "tell me about ",
)
BEGINNER_INTENT_PHRASES = (
    "in simple terms",
    "simply",
    "basic explanation",
    "beginner",
)


def _has_advanced_intent(text_lower: str) -> bool:
    return any(marker in text_lower for marker in ADVANCED_INTENT_MARKERS)


def _has_beginner_intent(text_lower: str) -> bool:
    if any(text_lower.startswith(prefix) for prefix in BEGINNER_INTENT_PREFIXES):
        return True
    if any(phrase in text_lower for phrase in BEGINNER_INTENT_PHRASES):
        return True
    tokens = text_lower.split()
    return text_lower.startswith("explain ") and len(tokens) <= 6


def predict_level(text):
    """
    Predict the learner difficulty level.

    The trained classifier is the primary signal. A narrow intent calibration is
    applied for definition/simple-explanation questions because those should be
    handled as beginner prompts unless the learner explicitly asks for advanced
    analysis. If the model is uncertain, the app falls back to "intermediate".
    """
    text_lower = str(text).lower().strip()
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = F.softmax(logits, dim=1)
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]
    predicted_label = CLASSIFIER_LABELS[pred_idx]

    if max(confidence) < LOW_CONFIDENCE_THRESHOLD:
        predicted_label = "intermediate"

    if _has_beginner_intent(text_lower) and not _has_advanced_intent(text_lower):
        predicted_label = "beginner"

    return predicted_label, confidence

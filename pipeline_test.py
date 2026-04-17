from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
import torch.nn.functional as F
from example_retriever import retrieve_examples, detect_best_topic

# -----------------------------
# Load classifier
# -----------------------------
tokenizer = DistilBertTokenizer.from_pretrained("./difficulty_classifier")
model = DistilBertForSequenceClassification.from_pretrained("./difficulty_classifier")
model.eval()

labels = ["beginner", "intermediate", "advanced"]

# -----------------------------
# Predict level
# -----------------------------
def predict_level(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    with torch.no_grad():
        logits = model(**inputs).logits

    probs = F.softmax(logits, dim=1)
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]
    predicted_label = labels[pred_idx]

    # fallback for uncertain predictions
    if max(confidence) < 0.6:
        predicted_label = "intermediate"

    return predicted_label, confidence

# -----------------------------
# Main pipeline test
# -----------------------------
if __name__ == "__main__":
    while True:
        q = input("\nEnter a student question (or quit): ").strip()
        if q.lower() == "quit":
            break

        # Step 1: classify difficulty
        level, confidence = predict_level(q)

        # Step 2: detect topic
        topic = detect_best_topic(q, level)

        # Step 3: retrieve examples
        examples = retrieve_examples(q, level, top_n=2)

        print("\n=== PIPELINE OUTPUT ===")
        print("Question:", q)
        print("Predicted Level:", level)
        print("Confidence (beginner, intermediate, advanced):", confidence)
        print("Detected Topic:", topic)

        print("\n=== RETRIEVED EXAMPLES ===")
        for i, row in enumerate(examples.itertuples(index=False), 1):
            print(f"\nExample {i}")
            print("Question:", row.question)
            print("Answer:", row.answer)
            print("Level:", row.level)
            print("Topic:", row.topic)
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import torch
import torch.nn.functional as F

# Load model
tokenizer = DistilBertTokenizer.from_pretrained("./difficulty_classifier")
model = DistilBertForSequenceClassification.from_pretrained("./difficulty_classifier")

model.eval()

labels = ["beginner", "intermediate", "advanced"]

def predict(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
    
    with torch.no_grad():
        logits = model(**inputs).logits

    # Convert to probabilities
    probs = F.softmax(logits, dim=1)
    
    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs.tolist()[0]

    predicted_label = labels[pred_idx]

    # 🔥 Smart fallback (important)
    max_conf = max(confidence)

    if max_conf < 0.6:
        predicted_label = "intermediate"

    return predicted_label, confidence


# Interactive testing loop
while True:
    q = input("\nEnter question (or quit): ")

    if q.lower() == "quit":
        break

    level, confidence = predict(q)

    print("Predicted Level:", level)
    print("Confidence (beginner, intermediate, advanced):", confidence)
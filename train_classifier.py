import os

os.environ["USE_TF"] = "0"

import pandas as pd
from datasets import Dataset
from transformers import (
    DistilBertTokenizer,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

# -------------------------
# Load cleaned dataset
# -------------------------
df = pd.read_csv("eduagent_training_ready.csv")

print("Total rows:", len(df))

# -------------------------
# Convert to HF dataset
# -------------------------
hf_data = Dataset.from_pandas(df[["question", "label"]])
hf_data = hf_data.rename_column("question", "text")

# -------------------------
# Train-test split (80-20)
# -------------------------
split = hf_data.train_test_split(test_size=0.2, seed=42)

print("Train size:", len(split["train"]))
print("Test size:", len(split["test"]))

# -------------------------
# Tokenization
# -------------------------
tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

def tokenize_fn(batch):
    return tokenizer(
        batch["text"],
        padding=True,
        truncation=True,
        max_length=128
    )

tokenized = split.map(tokenize_fn, batched=True)

# -------------------------
# Load model
# -------------------------
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=3
)

# -------------------------
# Metrics
# -------------------------
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, preds)}

# -------------------------
# Training config
# -------------------------
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    eval_strategy="epoch",
    save_strategy="epoch",
    logging_dir="./logs",
    logging_steps=10,
    load_best_model_at_end=True
)

# -------------------------
# Trainer
# -------------------------
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized["train"],
    eval_dataset=tokenized["test"],
    compute_metrics=compute_metrics
)

# -------------------------
# Train
# -------------------------
trainer.train()

# -------------------------
# Evaluate
# -------------------------
results = trainer.evaluate()
print("\nFinal Accuracy:", results["eval_accuracy"])

# -------------------------
# Detailed report
# -------------------------
predictions = trainer.predict(tokenized["test"])
preds = np.argmax(predictions.predictions, axis=-1)

print("\nClassification Report:")
print(classification_report(predictions.label_ids, preds))

# -------------------------
# Save model
# -------------------------
model.save_pretrained("./difficulty_classifier")
tokenizer.save_pretrained("./difficulty_classifier")

print("\nModel saved to ./difficulty_classifier")
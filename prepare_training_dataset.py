import pandas as pd

# Load dataset
df = pd.read_csv("eduagent_dataset.csv")

print("=== Original Dataset Info ===")
print("Columns:", df.columns.tolist())
print("Total rows:", len(df))

# Keep only required columns
df = df[["question", "level"]].copy()

# Remove rows with missing values
df = df.dropna(subset=["question", "level"])

# Clean text
df["question"] = df["question"].astype(str).str.strip()
df["level"] = df["level"].astype(str).str.strip().str.lower()

# Keep only valid labels
valid_levels = ["beginner", "intermediate", "advanced"]
df = df[df["level"].isin(valid_levels)]

# Remove empty questions
df = df[df["question"] != ""]

# Remove duplicate questions
df = df.drop_duplicates(subset=["question"])

# Map labels to numbers
label_map = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2
}
df["label"] = df["level"].map(label_map)

print("\n=== Cleaned Dataset Info ===")
print("Total rows after cleaning:", len(df))
print("\nLabel distribution:")
print(df["level"].value_counts())

print("\nSample rows:")
print(df.head())

# Save cleaned training file
df.to_csv("eduagent_training_ready.csv", index=False)

print("\nSaved cleaned file as: eduagent_training_ready.csv")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
df = pd.read_csv('eduagent_dataset.csv')

print("=== BASIC INFO ===")
print(df.head())
print("\nColumns:", df.columns)
print("\nTotal rows:", len(df))

# -----------------------------
# Graph 1: Level Distribution
# -----------------------------
plt.figure()
df['level'].value_counts().plot(kind='bar')
plt.title('Distribution of Difficulty Levels')
plt.xlabel('Level')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('graph1_levels.png')
plt.close()

# -----------------------------
# Graph 2: Topic Distribution
# -----------------------------
plt.figure(figsize=(10, 8))
df['topic'].value_counts().plot(kind='barh')
plt.title('Questions per Topic')
plt.tight_layout()
plt.savefig('graph2_topics.png')
plt.close()

# -----------------------------
# Graph 3: Answer Length by Level
# -----------------------------
df['answer_length'] = df['answer'].apply(lambda x: len(str(x).split()))

plt.figure()
df.groupby('level')['answer_length'].mean().plot(kind='bar')
plt.title('Average Answer Length by Level')
plt.xlabel('Level')
plt.ylabel('Average Word Count')
plt.tight_layout()
plt.savefig('graph3_lengths.png')
plt.close()

# -----------------------------
# Statistics
# -----------------------------
print("\n=== DATASET STATS ===")
print("Levels:", df['level'].unique())
print("Topics:", df['topic'].nunique())
print("\nAnswer Length Stats:")
print(df.groupby('level')['answer_length'].describe())
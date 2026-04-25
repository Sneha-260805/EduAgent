"""
Compatibility wrappers for older interactive scripts.

The active retrieval implementation lives in `ml.topic_detector` and
`ml.retriever`. This module keeps the previous import path working without
duplicating stale TF-IDF logic.
"""

from ml.retriever import df, retrieve_examples as _retrieve_examples
from ml.topic_detector import detect_best_topic as _detect_best_topic


def detect_best_topic(user_question, level):
    return _detect_best_topic(user_question, level, df)


def retrieve_examples(user_question, level, top_n=3):
    return _retrieve_examples(user_question, level, top_n=top_n)


if __name__ == "__main__":
    while True:
        q = input("\nEnter a student question (or quit): ").strip()
        if q.lower() == "quit":
            break

        level = input("Enter predicted level (beginner/intermediate/advanced): ").strip().lower()

        best_topic = detect_best_topic(q, level)
        print(f"\nDetected Topic: {best_topic}")

        results = retrieve_examples(q, level, top_n=3)

        print("\n=== Retrieved Examples ===")
        for i, row in enumerate(results.itertuples(index=False), 1):
            print(f"\nExample {i}")
            print("Question:", row.question)
            print("Answer:", row.answer)
            print("Level:", row.level)
            print("Topic:", row.topic)

from ml.classifier import predict_level
from ml.retriever import df, retrieve_examples
from ml.topic_detector import detect_best_topic


def print_pipeline_result(question: str):
    level, confidence = predict_level(question)
    topic = detect_best_topic(question, level, df)
    examples = retrieve_examples(question, level, top_n=2)

    print("\n=== PIPELINE OUTPUT ===")
    print("Question:", question)
    print("Predicted Level:", level)
    print("Confidence (beginner, intermediate, advanced):", confidence)
    print("Detected Topic:", topic)

    print("\n=== RETRIEVED EXAMPLES ===")
    if len(examples) == 0:
        print("No examples retrieved.")
        return

    for i, row in enumerate(examples.itertuples(index=False), 1):
        print(f"\nExample {i}")
        print("Question:", row.question)
        print("Answer:", row.answer)
        print("Level:", row.level)
        print("Topic:", row.topic)


if __name__ == "__main__":
    while True:
        q = input("\nEnter a student question (or quit): ").strip()
        if q.lower() == "quit":
            break
        print_pipeline_result(q)

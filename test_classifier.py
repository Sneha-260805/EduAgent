from ml.classifier import predict_level


if __name__ == "__main__":
    while True:
        q = input("\nEnter question (or quit): ").strip()
        if q.lower() == "quit":
            break

        level, confidence = predict_level(q)
        print("Predicted Level:", level)
        print("Confidence (beginner, intermediate, advanced):", confidence)

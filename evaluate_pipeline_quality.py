import argparse
import json
from datetime import datetime
from pathlib import Path

from agents.memory_agent import ensure_profile_structure
from agents.tutor_agent import generate_tutor_response


EVAL_CASES = [
    {
        "case_id": "beginner_supervised_learning",
        "question": "What is supervised learning in simple terms?",
        "profile": ensure_profile_structure({}),
        "notes": "Checks whether the tutor gives a simple, beginner-friendly explanation.",
    },
    {
        "case_id": "advanced_backpropagation",
        "question": "Analyze how backpropagation uses gradients to optimize neural network weights.",
        "profile": ensure_profile_structure({}),
        "notes": "Checks whether the tutor gives a more technical answer for an advanced-style question.",
    },
    {
        "case_id": "memory_weak_area",
        "question": "Explain gradient descent again.",
        "profile": ensure_profile_structure(
            {
                "topic_counts": {"Gradient Descent": 3},
                "topics_seen": ["Gradient Descent"],
                "weak_areas": {"Gradient Descent": ["learning rate", "local minima"]},
                "mastery": {"Gradient Descent": 0.25},
                "last_evaluation": {
                    "topic": "Gradient Descent",
                    "understanding_level": "poor",
                    "weak_concepts": ["learning rate", "local minima"],
                    "feedback": "The learner is confused about step size and optimization behavior.",
                    "recommended_action": "give easier example",
                },
            }
        ),
        "notes": "Checks whether memory changes the answer style and focuses on weak concepts.",
    },
]


def run_eval(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = []

    for case in EVAL_CASES:
        level, confidence, topic, examples, answer = generate_tutor_response(
            case["question"],
            case["profile"],
        )
        records.append(
            {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "case_id": case["case_id"],
                "notes": case["notes"],
                "question": case["question"],
                "predicted_level": level,
                "confidence": confidence,
                "detected_topic": topic,
                "retrieved_examples": examples.to_dict(orient="records"),
                "answer": answer,
            }
        )

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return records


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run a lightweight qualitative evaluation of EduAgent's tutor pipeline. "
            "This calls the live LLM and writes JSONL records for manual comparison."
        )
    )
    parser.add_argument(
        "--output",
        default="evaluation_runs/pipeline_eval.jsonl",
        help="Path for JSONL evaluation output.",
    )
    args = parser.parse_args()

    records = run_eval(Path(args.output))
    print(f"Wrote {len(records)} evaluation records to {args.output}")
    print("Review whether level, topic, retrieved examples, and answer style match each case.")


if __name__ == "__main__":
    main()

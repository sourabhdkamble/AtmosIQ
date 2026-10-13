
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Allow imports from the backend application.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.agents.supervisor import route_user_request  # noqa: E402


DATA_DIR = Path(__file__).resolve().parent
EVAL_FILE = DATA_DIR / "intent_eval.jsonl"
REPORT_FILE = DATA_DIR / "supervisor_evaluation_report.json"


def load_examples() -> list[dict]:
    """Load and validate the evaluation dataset."""

    examples = []

    with EVAL_FILE.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            if not isinstance(item.get("text"), str) or not item["text"].strip():
                raise ValueError(
                    f"Missing request text on line {line_number}"
                )

            if not isinstance(item.get("route"), str):
                raise ValueError(
                    f"Missing expected route on line {line_number}"
                )

            examples.append(item)

    return examples


def main() -> None:
    examples = load_examples()

    total = len(examples)
    correct = 0
    route_counts = Counter()
    route_correct = Counter()
    confusion = defaultdict(Counter)
    errors = []

    for item in examples:
        expected = item["route"]
        predicted = route_user_request(item["text"])

        route_counts[expected] += 1
        confusion[expected][predicted] += 1

        if predicted == expected:
            correct += 1
            route_correct[expected] += 1
        else:
            errors.append({
                "text": item["text"],
                "expected": expected,
                "predicted": predicted,
            })

    accuracy = correct / total if total else 0.0

    print("\n=== AtmosIQ Supervisor Evaluation ===")
    print(f"Examples evaluated: {total}")
    print(f"Correct predictions: {correct}")
    print(f"Incorrect predictions: {len(errors)}")
    print(f"Accuracy: {accuracy:.2%}")

    print("\n=== Per-route results ===")

    for route in sorted(route_counts):
        count = route_counts[route]
        route_accuracy = route_correct[route] / count
        print(
            f"{route}: {route_correct[route]}/{count} "
            f"correct ({route_accuracy:.2%})"
        )

    print("\n=== Misclassified examples ===")

    if not errors:
        print("No misclassifications.")
    else:
        for error in errors:
            print(f"\nText: {error['text']}")
            print(f"Expected: {error['expected']}")
            print(f"Predicted: {error['predicted']}")

    report = {
        "total_examples": total,
        "correct_predictions": correct,
        "incorrect_predictions": len(errors),
        "accuracy": accuracy,
        "per_route": {
            route: {
                "total": route_counts[route],
                "correct": route_correct[route],
                "accuracy": route_correct[route] / route_counts[route],
            }
            for route in sorted(route_counts)
        },
        "confusion_matrix": {
            expected: dict(predictions)
            for expected, predictions in sorted(confusion.items())
        },
        "errors": errors,
    }

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nReport saved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()

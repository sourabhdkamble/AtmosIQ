import json
import sys
from pathlib import Path

# Allow imports from backend
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.agents.supervisor import route_user_request, VALID_ROUTES

DATA_FILE = PROJECT_ROOT / "data" / "training" / "challenge_eval_25.json"
OUT_FILE = PROJECT_ROOT / "data" / "training" / "challenge_eval_25_baseline_predictions.json"

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    correct = 0
    results = []
    print("\n=== AtmosIQ Supervisor Baseline on 25 Challenge Prompts ===")
    
    for item in items:
        text = item["text"]
        expected = item["expected_route"]
        predicted = route_user_request(text)
        assert predicted in VALID_ROUTES, f"Invalid route predicted: {predicted}"
        
        is_correct = (predicted == expected)
        if is_correct:
            correct += 1
            
        status = "PASS" if is_correct else "FAIL"
        print(f"[{status}] ID {item['id']:02d}: Expected: {expected:<16} | Predicted: {predicted:<16} | '{text}'")
        results.append({
            "id": item["id"],
            "text": text,
            "category": item["category"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "notes": item.get("notes", "")
        })

    accuracy = correct / len(items)
    print(f"\nBaseline Score: {correct}/{len(items)} correct ({accuracy:.2%})")

    report = {
        "dataset": str(DATA_FILE),
        "total_prompts": len(items),
        "correct_predictions": correct,
        "accuracy": accuracy,
        "results": results
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to: {OUT_FILE}")

if __name__ == "__main__":
    main()

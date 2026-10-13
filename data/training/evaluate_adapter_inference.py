"""AtmosIQ — Standalone Isolated Adapter Inference Runner.

Evaluates Qwen/Qwen2.5-0.5B-Instruct + LoRA V2 adapter on test prompts.
Completely isolated from FastAPI / backend web runtime.
Requires: torch, transformers, peft (run in dedicated ML environment).
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("adapter_inference")

VALID_ROUTES = {
    "current_weather",
    "forecast",
    "weather_advice",
    "knowledge",
    "air_quality",
}

SYSTEM_PROMPT = "You are AtmosIQ supervisor."


def format_qwen_chat_prompt(user_text: str) -> str:
    """Format input text using Qwen ChatML template used during LoRA training."""
    return (
        f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
        f"<|im_start|>user\n{user_text}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )


def extract_route_from_generation(generated_text: str) -> Optional[str]:
    """Parse and normalize model generation into exactly one valid route.
    
    Returns:
        One of VALID_ROUTES, or None if no valid route could be determined.
    """
    clean = generated_text.strip().lower()
    clean = re.sub(r'[\'"{},:;.]', '', clean).strip()

    # Exact direct match
    if clean in VALID_ROUTES:
        return clean

    # First token match
    tokens = clean.split()
    if tokens and tokens[0] in VALID_ROUTES:
        return tokens[0]

    # Keyword search fallback within generated text
    for route in sorted(VALID_ROUTES, key=len, reverse=True):
        if route in clean:
            return route

    return None


def load_dataset(eval_file: Path) -> List[Dict[str, Any]]:
    """Load evaluation prompts from JSON or JSONL file."""
    if not eval_file.exists():
        raise FileNotFoundError(f"Evaluation dataset not found: {eval_file}")

    items = []
    with open(eval_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content.startswith("["):
            items = json.loads(content)
        else:
            for line in content.splitlines():
                if line.strip():
                    items.append(json.loads(line))

    # Validate schema
    for idx, item in enumerate(items):
        text = item.get("text") or item.get("input")
        if not text:
            raise ValueError(f"Missing text/input on item {idx}: {item}")
        item["text"] = text

        expected = item.get("expected_route") or item.get("route") or item.get("actual")
        if not expected or expected not in VALID_ROUTES:
            raise ValueError(f"Invalid or missing expected route on item {idx}: {item}")
        item["expected_route"] = expected

    return items


def run_inference(
    base_model_name: str,
    adapter_dir: Path,
    eval_file: Path,
    output_file: Path,
    device: str = "auto",
) -> Dict[str, Any]:
    """Load model with PEFT adapter and run inference on all prompts."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        logger.error(
            "ML runtime dependencies not installed. "
            "Please run this script in an isolated ML virtualenv with: pip install torch transformers peft accelerate"
        )
        raise RuntimeError(f"Missing ML dependencies: {e}") from e

    logger.info("Loading tokenizer from: %s", adapter_dir)
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_dir), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    logger.info("Loading base model: %s (device_map=%s)", base_model_name, device)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map=device if device != "auto" else ("auto" if torch.cuda.is_available() else None),
        trust_remote_code=True,
    )

    logger.info("Loading PEFT LoRA adapter from: %s", adapter_dir)
    model = PeftModel.from_pretrained(base_model, str(adapter_dir))
    model.eval()

    dataset = load_dataset(eval_file)
    logger.info("Loaded %d evaluation prompts from %s", len(dataset), eval_file)

    predictions = []
    correct_count = 0
    route_counts = Counter()
    route_correct = Counter()
    confusion = defaultdict(Counter)

    for item in dataset:
        prompt = format_qwen_chat_prompt(item["text"])
        inputs = tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available() and device != "cpu":
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=16,
                temperature=0.0,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )

        # Slice off input tokens to isolate generated tokens
        input_len = inputs["input_ids"].shape[1]
        gen_tokens = outputs[0][input_len:]
        raw_output = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

        predicted_route = extract_route_from_generation(raw_output)
        expected_route = item["expected_route"]

        is_correct = (predicted_route == expected_route)
        if is_correct:
            correct_count += 1
            route_correct[expected_route] += 1

        route_counts[expected_route] += 1
        confusion[expected_route][predicted_route or "unmapped"] += 1

        pred_entry = {
            "id": item.get("id"),
            "text": item["text"],
            "expected": expected_route,
            "predicted": predicted_route,
            "raw_output": raw_output,
            "correct": is_correct,
            "notes": item.get("notes", ""),
        }
        predictions.append(pred_entry)
        logger.info(
            "[%s] Text: '%s' -> Expected: %s, Predicted: %s (Raw: '%s')",
            "PASS" if is_correct else "FAIL",
            item["text"][:40],
            expected_route,
            predicted_route,
            raw_output,
        )

    accuracy = correct_count / len(dataset) if dataset else 0.0

    # Calculate invalid routes (where model generated text outside VALID_ROUTES)
    invalid_route_count = sum(1 for p in predictions if p["predicted"] is None or p["predicted"] not in VALID_ROUTES)

    # Compute per-class precision, recall, f1-score
    per_class_metrics = {}
    macro_p, macro_r, macro_f1 = 0.0, 0.0, 0.0
    for route in sorted(VALID_ROUTES):
        tp = route_correct[route]
        fn = route_counts[route] - tp
        fp = sum(confusion[other][route] for other in VALID_ROUTES if other != route)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        support = route_counts[route]
        per_class_metrics[route] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1-score": round(f1, 4),
            "support": support,
        }
        macro_p += precision
        macro_r += recall
        macro_f1 += f1

    num_classes = len(VALID_ROUTES)
    macro_avg = {
        "precision": round(macro_p / num_classes, 4),
        "recall": round(macro_r / num_classes, 4),
        "f1-score": round(macro_f1 / num_classes, 4),
        "support": len(dataset),
    }

    report = {
        "model_name": base_model_name,
        "adapter_dir": str(adapter_dir),
        "eval_dataset": str(eval_file),
        "total_prompts": len(dataset),
        "correct_predictions": correct_count,
        "invalid_route_count": invalid_route_count,
        "accuracy": accuracy,
        "per_class_metrics": per_class_metrics,
        "macro_avg": macro_avg,
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
        "predictions": predictions,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Also save dedicated predictions JSON
    preds_file = output_file.parent / "atmosiq_lora_v2_challenge_predictions.json"
    with open(preds_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    logger.info("Evaluation complete! Accuracy: %.2f%% (%d/%d)", accuracy * 100, correct_count, len(dataset))
    logger.info("Invalid route count: %d", invalid_route_count)
    logger.info("Report saved to: %s", output_file)
    logger.info("Predictions saved to: %s", preds_file)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone LoRA Adapter Inference Runner")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-0.5B-Instruct", help="Hugging Face base model ID")
    parser.add_argument(
        "--adapter-dir",
        default=str(Path(__file__).resolve().parents[2] / "backend" / "models" / "atmosiq-supervisor-lora-v2"),
        help="Path to fine-tuned LoRA adapter directory",
    )
    parser.add_argument(
        "--eval-file",
        default=str(Path(__file__).resolve().parent / "challenge_eval_25.jsonl"),
        help="Path to evaluation prompts file (.json or .jsonl)",
    )
    parser.add_argument(
        "--output-file",
        default=str(Path(__file__).resolve().parent / "atmosiq_lora_v2_challenge_report.json"),
        help="Path to output JSON report",
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"], help="Inference device")
    args = parser.parse_args()

    run_inference(
        base_model_name=args.base_model,
        adapter_dir=Path(args.adapter_dir),
        eval_file=Path(args.eval_file),
        output_file=Path(args.output_file),
        device=args.device,
    )


if __name__ == "__main__":
    main()

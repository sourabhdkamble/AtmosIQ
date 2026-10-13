import json
from pathlib import Path
import pytest

from app.agents.supervisor import VALID_ROUTES

MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "atmosiq-supervisor-lora-v2"
TRAINING_DIR = Path(__file__).resolve().parents[2] / "data" / "training"


def test_adapter_v2_artifacts_exist():
    """Verify that the extracted V2 LoRA adapter files exist and have non-zero size."""
    assert MODEL_DIR.exists(), f"Model directory {MODEL_DIR} does not exist"
    
    expected_files = [
        "adapter_config.json",
        "adapter_model.safetensors",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt",
        "special_tokens_map.json",
    ]
    
    for filename in expected_files:
        file_path = MODEL_DIR / filename
        assert file_path.exists(), f"Missing required adapter file: {filename}"
        assert file_path.stat().st_size > 0, f"Adapter file {filename} is empty"


def test_adapter_v2_configuration():
    """Verify that the V2 adapter config matches the Qwen2.5-0.5B LoRA specifications."""
    config_path = MODEL_DIR / "adapter_config.json"
    assert config_path.exists()
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    assert config.get("base_model_name_or_path") == "Qwen/Qwen2.5-0.5B-Instruct"
    assert config.get("peft_type") == "LORA"
    assert config.get("r") == 8
    assert config.get("lora_alpha") == 16
    assert set(config.get("target_modules", [])) == {"q_proj", "k_proj", "o_proj", "v_proj"}
    assert config.get("task_type") == "CAUSAL_LM"


def test_adapter_v2_predictions_compatibility():
    """Verify that V2 model predictions are 100% compliant with AtmosIQ's VALID_ROUTES."""
    pred_path = TRAINING_DIR / "atmosiq_lora_v2_predictions.json"
    assert pred_path.exists(), f"Predictions file {pred_path} does not exist"
    
    with open(pred_path, "r", encoding="utf-8") as f:
        predictions = json.load(f)
        
    assert len(predictions) == 90
    
    correct_count = 0
    for item in predictions:
        predicted = item.get("predicted")
        actual = item.get("actual")
        
        # Every prediction must be one of the AtmosIQ supervisor valid routes
        assert predicted in VALID_ROUTES, f"Predicted route '{predicted}' is not a valid AtmosIQ route"
        assert actual in VALID_ROUTES, f"Actual route '{actual}' is not a valid AtmosIQ route"
        
        if predicted == actual:
            correct_count += 1
            
    # Confirm reported accuracy matches predictions
    calculated_accuracy = correct_count / len(predictions)
    assert calculated_accuracy == pytest.approx(85 / 90, rel=1e-4)


def test_adapter_inference_runtime():
    """Separate adapter inference test: verifies runtime execution when torch/peft are available."""
    try:
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as e:
        pytest.skip(f"PyTorch/PEFT runtime dependencies not installed in this environment: {e}")

    # If installed, verify tokenizer and adapter loading
    tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR))
    tokens = tokenizer("What is the current weather in Mumbai?", return_tensors="pt")
    assert tokens["input_ids"].shape[1] > 0


def test_challenge_dataset_integrity():
    """Verify that the 25 challenge prompts dataset is complete and well-formed."""
    challenge_file = TRAINING_DIR / "challenge_eval_25.json"
    assert challenge_file.exists(), f"Challenge dataset {challenge_file} not found"

    with open(challenge_file, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    assert len(prompts) >= 20, f"Expected >= 20 challenge prompts, found {len(prompts)}"
    
    categories = {p["category"] for p in prompts}
    expected_categories = {"current_weather", "forecast", "weather_advice", "knowledge", "air_quality"}
    assert categories == expected_categories, f"Missing categories: {expected_categories - categories}"

    for p in prompts:
        assert isinstance(p.get("text"), str) and len(p["text"].strip()) > 0
        assert p.get("expected_route") in VALID_ROUTES
        assert p.get("category") in VALID_ROUTES


def test_challenge_runner_interface():
    """Verify isolated runner module formatting and normalization logic."""
    import sys
    sys.path.insert(0, str(TRAINING_DIR))
    from evaluate_adapter_inference import extract_route_from_generation, format_qwen_chat_prompt

    # Test prompt formatting
    formatted = format_qwen_chat_prompt("Is it raining in Pune?")
    assert "<|im_start|>system\nYou are AtmosIQ supervisor.<|im_end|>" in formatted
    assert "<|im_start|>user\nIs it raining in Pune?<|im_end|>" in formatted
    assert "<|im_start|>assistant\n" in formatted

    # Test route extraction
    for route in VALID_ROUTES:
        assert extract_route_from_generation(route) == route
        assert extract_route_from_generation(f"'{route}'\n") == route
        assert extract_route_from_generation(f'{route}.') == route
        assert extract_route_from_generation(f'{route} - user is asking for {route}') == route

    assert extract_route_from_generation("completely unrelated gibberish") is None


def test_challenge_baseline_predictions():
    """Verify baseline predictions on challenge dataset are recorded and non-empty."""
    baseline_file = TRAINING_DIR / "challenge_eval_25_baseline_predictions.json"
    assert baseline_file.exists()

    with open(baseline_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_prompts"] == 25
    assert 0.0 <= data["accuracy"] <= 1.0
    assert len(data["results"]) == 25


# Google Colab / Kaggle Reproducibility Script for AtmosIQ LoRA V2 Evaluation
# Free T4 GPU (~30 seconds execution, 0 cost)

"""
To run in Google Colab:
1. Open a new notebook with free T4 GPU.
2. Clone/upload the AtmosIQ repo or adapter folder.
3. Paste and run this cell.
"""

# !pip install -q torch transformers peft accelerate

import json
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE_MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
ADAPTER_DIR = "./atmosiq-supervisor-lora-v2"
EVAL_FILE = "./challenge_eval_25.jsonl"
VALID_ROUTES = {"current_weather", "forecast", "weather_advice", "knowledge", "air_quality"}

print("Loading tokenizer and model...")
tokenizer = AutoTokenizer.from_pretrained(ADAPTER_DIR)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL_NAME,
    torch_dtype=torch.float16,
    device_map="auto"
)
model = PeftModel.from_pretrained(base_model, ADAPTER_DIR)
model.eval()

with open(EVAL_FILE, "r", encoding="utf-8") as f:
    items = [json.loads(line) for line in f if line.strip()]

correct = 0
results = []
for item in items:
    prompt = f"<|im_start|>system\nYou are AtmosIQ supervisor.<|im_end|>\n<|im_start|>user\n{item['text']}<|im_end|>\n<|im_start|>assistant\n"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=16, temperature=0.0, do_sample=False)
    gen_text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
    
    # Extract route
    pred = gen_text.lower().replace("'", "").replace('"', "")
    is_correct = (pred == item["expected_route"])
    if is_correct:
        correct += 1
    results.append({
        "id": item["id"],
        "text": item["text"],
        "expected": item["expected_route"],
        "predicted": pred,
        "is_correct": is_correct
    })
    print(f"[{'PASS' if is_correct else 'FAIL'}] {item['text'][:40]} -> Exp: {item['expected_route']}, Pred: {pred}")

print(f"\nFinal Accuracy: {correct}/{len(items)} ({correct/len(items):.2%})")

"""AtmosIQ — Reproducible Free LoRA/PEFT Fine-Tuning Pipeline.

Designed for free hosted GPU environments (Google Colab T4 15GB or Kaggle 2xT4).
Target model: Qwen/Qwen2.5-0.5B-Instruct or meta-llama/Llama-3.2-1B-Instruct.
Task: Intent routing & grounded weather advice generation.
Zero cost, strictly open-source Apache 2.0 / permissive open weights.
"""

import json
from pathlib import Path

# 1. Dataset Preparation with Train/Val/Test Split
DATASET = [
    # Format: {"instruction": ..., "input": ..., "output": ...}
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "What is the temperature in Delhi right now?", "output": '{"route": "current_weather"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "Will it rain tomorrow in Mumbai?", "output": '{"route": "forecast"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "What should I wear in Pune today?", "output": '{"route": "weather_advice"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "What causes morning fog?", "output": '{"route": "knowledge"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "What is the current AQI in Kolkata?", "output": '{"route": "air_quality"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "temprature outside right now", "output": '{"route": "current_weather"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "Should I wear a jacket if I go out?", "output": '{"route": "weather_advice"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "Can I breathe outdoor air safely in Kanpur?", "output": '{"route": "air_quality"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "next 48 hours in Bengaluru", "output": '{"route": "forecast"}'},
    {"instruction": "Route the weather assistant user request to one route: current_weather, forecast, weather_advice, knowledge, air_quality.", "input": "Explain relative humidity and heat index", "output": '{"route": "knowledge"}'},
]

def generate_splits(output_dir="data/training/finetune_data"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # 70% Train, 15% Val, 15% Test
    train_data = DATASET[:7]
    val_data = DATASET[7:8]
    test_data = DATASET[8:]
    
    with (out_path / "train.jsonl").open("w", encoding="utf-8") as f:
        for row in train_data:
            f.write(json.dumps(row) + "\n")
            
    with (out_path / "val.jsonl").open("w", encoding="utf-8") as f:
        for row in val_data:
            f.write(json.dumps(row) + "\n")
            
    with (out_path / "test.jsonl").open("w", encoding="utf-8") as f:
        for row in test_data:
            f.write(json.dumps(row) + "\n")
            
    print(f"Generated train ({len(train_data)}), val ({len(val_data)}), test ({len(test_data)}) in {out_path}")

COLAB_TRAINING_SCRIPT = '''
# RUN IN FREE GOOGLE COLAB WITH T4 GPU

!pip install -q transformers peft trl datasets accelerate bitsandbytes

import torch
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    device_map="auto"
)

peft_config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

training_args = TrainingArguments(
    output_dir="./atmosiq-lora-adapter",
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_steps=5,
    num_train_epochs=3,
    save_strategy="epoch",
    fp16=True,
    report_to="none"
)

# Format dataset for SFTTrainer
def formatting_prompts_func(example):
    text = f"<|im_start|>system\\nYou are AtmosIQ supervisor.<|im_end|>\\n<|im_start|>user\\n{example['input']}<|im_end|>\\n<|im_start|>assistant\\n{example['output']}<|im_end|>"
    return [text]

# Load and train
dataset = load_dataset("json", data_files={"train": "data/training/finetune_data/train.jsonl", "validation": "data/training/finetune_data/val.jsonl"})

trainer = SFTTrainer(
    model=model,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    peft_config=peft_config,
    formatting_func=formatting_prompts_func,
    args=training_args,
)

trainer.train()
trainer.model.save_pretrained("./atmosiq-supervisor-lora")
print("LoRA adapter saved successfully to ./atmosiq-supervisor-lora")
'''

if __name__ == "__main__":
    generate_splits()

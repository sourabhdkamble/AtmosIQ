import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
EVAL_FILE = DATA_DIR / "intent_eval.jsonl"

CHALLENGE_EXAMPLES = [
    # Current weather
    {"text": "Would I need a fan in Panvel at the moment?", "route": "current_weather"},
    {"text": "Give me a quick picture of the conditions outside in Pune right now.", "route": "current_weather"},
    {"text": "Is the weather outside comfortable enough for a short walk in Nashik?", "route": "current_weather"},
    {"text": "What's it like outdoors in Mumbai at this very moment?", "route": "current_weather"},
    {"text": "Can you check whether the sky is clear in Delhi right now?", "route": "current_weather"},
    {"text": "Tell me the present conditions, not tomorrow's forecast, for Bengaluru.", "route": "current_weather"},

    # Forecast
    {"text": "Will my clothes dry outside in Panvel tomorrow?", "route": "forecast"},
    {"text": "I have an outdoor event in Pune two days from now. What conditions are expected?", "route": "forecast"},
    {"text": "Show me how the temperature changes throughout the day in Mumbai.", "route": "forecast"},
    {"text": "What kind of weather should I expect over the coming weekend in Goa?", "route": "forecast"},
    {"text": "Give me the weather outlook for the next 48 hours in Delhi.", "route": "forecast"},
    {"text": "Will rain be a concern later this evening in Bengaluru?", "route": "forecast"},

    # Weather advice
    {"text": "I'm commuting by motorcycle. How should I prepare for the weather in Pune?", "route": "weather_advice"},
    {"text": "Would you recommend lightweight clothes or layers for a day outside in Shimla?", "route": "weather_advice"},
    {"text": "I plan to walk my dog outdoors. What precautions should I take in Mumbai?", "route": "weather_advice"},
    {"text": "What should I keep in my bag for a day with unpredictable weather in Panvel?", "route": "weather_advice"},
    {"text": "Is there anything I should do to protect myself during very hot conditions?", "route": "weather_advice"},
    {"text": "Help me decide whether to move my outdoor workout indoors because of the weather.", "route": "weather_advice"},

    # General weather knowledge
    {"text": "Why can two nearby cities have different temperatures at the same time?", "route": "knowledge"},
    {"text": "What is the difference between humidity and the chance of rain?", "route": "knowledge"},
    {"text": "How do meteorologists estimate the probability of precipitation?", "route": "knowledge"},
    {"text": "Why does the temperature usually fall after sunset?", "route": "knowledge"},
    {"text": "What causes a sea breeze to develop during the day?", "route": "knowledge"},
    {"text": "Can you explain the difference between climate and weather in simple terms?", "route": "knowledge"},

    # Air quality
    {"text": "Would breathing outdoor air in Delhi expose me to high PM2.5 levels today?", "route": "air_quality"},
    {"text": "How can I find out whether pollution levels are unhealthy in Mumbai?", "route": "air_quality"},
    {"text": "Is particulate matter the same thing as ordinary dust?", "route": "air_quality"},
    {"text": "What does an AQI reading tell me about the air I breathe?", "route": "air_quality"},
    {"text": "Can you check the pollution situation in Pune, especially PM10?", "route": "air_quality"},
    {"text": "Should people with outdoor jobs pay attention to today's air pollution levels?", "route": "air_quality"},
]


def main():
    if not EVAL_FILE.exists():
        raise FileNotFoundError(f"Evaluation file not found: {EVAL_FILE}")

    existing = []
    with EVAL_FILE.open("r", encoding="utf-8-sig") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {exc}"
                ) from exc

            if not isinstance(record.get("text"), str) or not isinstance(
                record.get("route"), str
            ):
                raise ValueError(
                    f"Line {line_number} must contain string fields "
                    "'text' and 'route'."
                )

            existing.append(record)

    existing_texts = {
        record["text"].strip().casefold()
        for record in existing
    }

    added = []
    skipped = 0

    for example in CHALLENGE_EXAMPLES:
        normalized_text = example["text"].strip().casefold()
        if normalized_text in existing_texts:
            skipped += 1
            continue

        added.append(example)
        existing_texts.add(normalized_text)

    all_records = existing + added

    # Write to a temporary file first, preserving the original if writing fails.
    temp_file = EVAL_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8", newline="\n") as file:
        for record in all_records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    temp_file.replace(EVAL_FILE)

    route_counts = {}
    for record in all_records:
        route = record["route"]
        route_counts[route] = route_counts.get(route, 0) + 1

    print(f"Evaluation file: {EVAL_FILE}")
    print(f"Existing records: {len(existing)}")
    print(f"New challenge examples added: {len(added)}")
    print(f"Duplicate examples skipped: {skipped}")
    print(f"Total evaluation examples: {len(all_records)}")
    print("Examples per route:")
    for route, count in sorted(route_counts.items()):
        print(f"  {route}: {count}")


if __name__ == "__main__":
    main()

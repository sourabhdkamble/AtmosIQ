
import json
import random
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent
TRAIN_FILE = DATA_DIR / "intent_examples.jsonl"
EVAL_FILE = DATA_DIR / "intent_eval.jsonl"

random.seed(42)

CITIES = [
    "Mumbai", "Panvel", "Pune", "Nashik", "Delhi", "Bengaluru",
    "Hyderabad", "Chennai", "Kolkata", "Jaipur", "Surat", "Nagpur",
]

EXAMPLES = {
    "current_weather": [
        "What's the temperature in {city} right now?",
        "Is it raining in {city} at the moment?",
        "Tell me the current weather in {city}.",
        "How hot is it outside in {city}?",
        "What's the weather like in {city} currently?",
        "Is it cloudy in {city} right now?",
        "Give me the current conditions for {city}.",
        "How windy is it in {city} at present?",
        "What's the temperature outside in {city} today?",
        "Check the current weather for {city}.",
    ],
    "forecast": [
        "What's the weather forecast for {city} tomorrow?",
        "Show me the next seven days in {city}.",
        "Give me the hourly forecast for {city}.",
        "Will it rain in {city} this weekend?",
        "What will the weather be like in {city} next week?",
        "Show the daily forecast for {city}.",
        "How will the weather change in {city} over the next few days?",
        "Will tomorrow be sunny in {city}?",
        "Give me the forecast for the coming days in {city}.",
        "What's expected in {city} over the next 24 hours?",
    ],
    "weather_advice": [
        "Should I carry an umbrella in {city} today?",
        "What should I wear in {city} given the weather?",
        "Is it safe to run outdoors in {city} today?",
        "What precautions should I take in {city} during a storm?",
        "Should I carry a raincoat in {city}?",
        "Is today a good day for a picnic in {city}?",
        "What should I carry when travelling in {city} today?",
        "How should I prepare for the heat in {city}?",
        "Would you recommend outdoor exercise in {city} today?",
        "What precautions should I take in {city} in strong winds?",
    ],
    "knowledge": [
        "Explain how humidity works.",
        "Why does wind make us feel colder?",
        "How are monsoons formed?",
        "What's the difference between weather and climate?",
        "Why do clouds form?",
        "How does air pressure affect weather?",
        "What causes thunderstorms?",
        "Explain the water cycle simply.",
        "Why does fog form in the morning?",
        "What causes a sea breeze?",
        "What is relative humidity?",
        "How do meteorologists predict rain?",
        "What is atmospheric pressure?",
        "Why is the sky blue?",
        "How does a rainbow form?",
        "What causes lightning?",
        "Why does thunder follow lightning?",
        "How do cyclones develop?",
        "What is the eye of a cyclone?",
        "How are hurricanes different from tornadoes?",
        "What is a heatwave?",
        "What causes a cold wave?",
        "How does wind speed affect weather?",
        "What is the dew point?",
        "Why does dew form on grass?",
        "What is cloud cover?",
        "How do clouds produce rain?",
        "What is precipitation?",
        "What is the difference between sleet and hail?",
        "How does snow form?",
        "Why does hail occur during storms?",
        "What is a weather front?",
        "What happens when a cold front arrives?",
        "What is a warm front?",
        "How does a monsoon trough work?",
        "Why does India have a monsoon season?",
        "What is El Nino?",
        "What is La Nina?",
        "How can ocean temperatures affect weather?",
        "What is the jet stream?",
        "Why do coastal areas have milder temperatures?",
        "How do mountains influence rainfall?",
        "What is the rain shadow effect?",
        "Why are deserts dry?",
        "How does evaporation affect the atmosphere?",
        "What is condensation?",
        "What is the greenhouse effect?",
        "How is climate change different from daily weather?",
        "What does a weather station measure?",
        "What is a barometer used for?",
        "How does a thermometer measure temperature?",
        "What is an anemometer?",
        "What does a rain gauge measure?",
        "What is a weather radar?",
        "How do weather satellites work?",
        "What is a weather warning?",
        "What does a yellow weather alert mean?",
        "What is the difference between a watch and a warning?",
        "Why can weather forecasts change?",
        "How accurate are seven-day forecasts?",
        "What does probability of precipitation mean?",
        "What is wind chill?",
        "What is the heat index?",
        "Why can the temperature feel different from the reading?",
        "How does humidity affect how hot we feel?",
        "Why does fog reduce visibility?",
        "What causes morning mist?",
        "How does sea fog develop?",
        "What is freezing rain?",
        "Why do some clouds look dark?",
        "What are cumulonimbus clouds?",
        "What are cirrus clouds?",
        "What are stratus clouds?",
        "How are clouds classified?",
        "What is atmospheric instability?",
        "What causes sudden gusts of wind?",
        "Why does wind direction matter?",
        "What is a pressure gradient?",
        "How does air move around high pressure?",
        "What is a low-pressure system?",
        "Why does low pressure often bring clouds?",
        "How do thunderstorms become severe?",
        "What is a dust storm?",
        "How do heatwaves affect the body?",
        "Why can nights stay warm during a heatwave?",
        "What causes urban heat islands?",
        "Why do cities sometimes receive intense rainfall?",
        "What is flash flooding?",
        "How does soil moisture affect flooding?",
        "Why can rainfall vary across nearby locations?",
        "What is seasonal forecasting?",
        "How is climate measured over decades?",
        "What is a normal climate baseline?",
        "Why do seasons occur?",
        "Why are days longer in summer?",
        "What causes winter fog in northern India?",
        "How does humidity influence monsoon rainfall?",
        "What is an atmospheric river?",
        "Why does hail form in strong thunderstorms?",
        "How do scientists classify tropical cyclones?",
        "What information goes into a weather forecast?",
    ],
    "air_quality": [
        "What's the AQI in {city} right now?",
        "Check PM2.5 levels in {city}.",
        "How polluted is the air in {city} today?",
        "What's the current air quality in {city}?",
        "Can you check today's AQI for {city}?",
        "Are pollution levels high in {city}?",
        "Give me the latest PM10 reading in {city}.",
        "Is the air safe to breathe in {city} today?",
        "What's the air pollution index in {city}?",
        "Check current particulate pollution in {city}.",
    ],
}


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


def save_jsonl(path: Path, examples: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for example in examples:
            file.write(json.dumps(example, ensure_ascii=False) + "\n")


def example_key(example: dict) -> tuple[str, str]:
    return (
        example["text"].strip().casefold(),
        example["route"],
    )


def generate_examples() -> list[dict]:
    generated = []

    for route, templates in EXAMPLES.items():
        for template in templates:
            if "{city}" in template:
                for city in CITIES:
                    generated.append({
                        "text": template.format(city=city),
                        "route": route,
                    })
            else:
                generated.append({
                    "text": template,
                    "route": route,
                })

    random.shuffle(generated)
    return generated


def main() -> None:
    training = load_jsonl(TRAIN_FILE)
    evaluation = load_jsonl(EVAL_FILE)

    existing = {
        example_key(item)
        for item in training + evaluation
    }

    new_examples = []

    for item in generate_examples():
        key = example_key(item)

        if key not in existing:
            new_examples.append(item)
            existing.add(key)

    training.extend(new_examples)
    save_jsonl(TRAIN_FILE, training)

    print(f"Training examples added: {len(new_examples)}")
    print(f"Total training examples: {len(training)}")
    print(f"Evaluation examples preserved: {len(evaluation)}")
    print("\nTraining examples by route:")

    from collections import Counter

    for route, count in sorted(
        Counter(item["route"] for item in training).items()
    ):
        print(f"  {route}: {count}")

    print(f"\nTraining file: {TRAIN_FILE}")
    print("Dataset expansion complete.")


if __name__ == "__main__":
    main()

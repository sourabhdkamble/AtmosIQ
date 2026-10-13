
import json
from pathlib import Path


EVAL_FILE = Path(__file__).resolve().parent / "intent_eval.jsonl"

EXAMPLES = {
    "current_weather": [
        "How warm is it in Thane right now?",
        "Is the sky cloudy over Aurangabad at the moment?",
        "Tell me the present temperature in Indore.",
        "What's the weather currently like in Kochi?",
        "Is there wind in Ahmedabad right now?",
        "Check current conditions in Bhopal.",
        "Is it raining in Visakhapatnam at present?",
        "How cold is it outside in Shimla right now?",
        "What's the current temperature in Goa?",
        "Describe the weather in Lucknow right now.",
    ],
    "forecast": [
        "What is expected in Thane tomorrow?",
        "Show the next five days of weather in Kochi.",
        "Will Ahmedabad get rain this weekend?",
        "Give me the hourly weather outlook for Indore.",
        "What will conditions be like in Goa next week?",
        "Is rain expected in Bhopal tomorrow?",
        "Show me the seven-day outlook for Lucknow.",
        "How will the weather change overnight in Shimla?",
        "Give me tomorrow's forecast for Visakhapatnam.",
        "What is the weather outlook for the next 48 hours in Pune?",
    ],
    "weather_advice": [
        "Should I take a jacket when going out in Shimla?",
        "Would today be suitable for cycling in Thane?",
        "What should I pack for a rainy day in Kochi?",
        "How can I stay comfortable during hot weather in Indore?",
        "Should I postpone a picnic because of the weather in Goa?",
        "What precautions are useful during heavy rain in Bhopal?",
        "Is outdoor exercise a good idea in Ahmedabad today?",
        "What footwear should I use in wet conditions?",
        "How should I prepare for strong winds while travelling?",
        "Should I protect myself from the sun this afternoon?",
    ],
    "knowledge": [
        "What is the difference between humidity and precipitation?",
        "Why do temperatures drop after sunset?",
        "How does a cyclone gain strength?",
        "What is the role of the jet stream?",
        "Why do coastal areas often have high humidity?",
        "How does Doppler weather radar work?",
        "What does dew point tell us?",
        "Why do clouds sometimes produce no rain?",
        "How is wind direction measured?",
        "What makes a thunderstorm severe?",
    ],
    "air_quality": [
        "Can you check the current AQI in Thane?",
        "What are the PM2.5 levels in Kochi today?",
        "Is the air pollution level high in Indore right now?",
        "Check the latest air quality index for Ahmedabad.",
        "What is the current PM10 concentration in Goa?",
        "How polluted is the air in Bhopal today?",
        "Can you provide a live AQI reading for Lucknow?",
        "Are particulate pollution levels elevated in Shimla?",
        "Check today's air quality in Visakhapatnam.",
        "What is the current pollution index in Nagpur?",
    ],
}


def main() -> None:
    existing = []

    if EVAL_FILE.exists():
        with EVAL_FILE.open("r", encoding="utf-8-sig") as file:
            existing = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

    seen = {
        (item["text"].strip().casefold(), item["route"])
        for item in existing
    }

    added = []

    for route, texts in EXAMPLES.items():
        for text in texts:
            item = {"text": text, "route": route}
            key = (text.casefold(), route)

            if key not in seen:
                added.append(item)
                seen.add(key)

    combined = existing + added

    with EVAL_FILE.open("w", encoding="utf-8") as file:
        for item in combined:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Evaluation examples added: {len(added)}")
    print(f"Total evaluation examples: {len(combined)}")
    print(f"Evaluation file: {EVAL_FILE}")


if __name__ == "__main__":
    main()

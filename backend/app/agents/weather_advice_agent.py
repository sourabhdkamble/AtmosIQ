import logging

from app.agents.weather_graph_llm import get_weather_llm

logger = logging.getLogger(__name__)


def generate_local_weather_advice(message: str, weather: dict) -> str:
    """Generate practical advice without calling an external AI model."""

    question = message.lower()
    advice = []

    temperature = weather.get("temperature_c")
    feels_like = weather.get("feels_like_c")
    humidity = weather.get("humidity_percent")
    wind = weather.get("wind_speed_kmh")
    precipitation = weather.get("precipitation_mm")
    description = str(weather.get("description", "")).lower()

    if temperature is None:
        return (
            "I couldn't retrieve enough weather measurements to give "
            "specific advice. Please try again later."
        )

    try:
        temperature = float(temperature)
        feels_like = float(feels_like) if feels_like is not None else temperature
        wind = float(wind) if wind is not None else None
        humidity = float(humidity) if humidity is not None else None
        precipitation = (
            float(precipitation) if precipitation is not None else None
        )
    except (TypeError, ValueError):
        return (
            "I couldn't interpret the available weather measurements "
            "reliably. Please try again later."
        )

    if feels_like >= 38 or temperature >= 38:
        advice.append(
            "It feels very hot. Wear lightweight clothing, drink water "
            "regularly, and limit strenuous outdoor activity."
        )
    elif feels_like >= 32 or temperature >= 32:
        advice.append(
            "Conditions are warm. Lightweight, breathable clothing "
            "should be comfortable, and staying hydrated is a good idea."
        )
    elif temperature <= 15:
        advice.append(
            "Conditions are cool. Consider a warm layer when going outside."
        )
    else:
        advice.append(
            "Choose comfortable clothing suitable for the conditions."
        )

    if precipitation is not None and precipitation > 0:
        advice.append(
            "Precipitation is being reported, so consider carrying "
            "an umbrella or raincoat."
        )
    elif any(term in description for term in ("rain", "drizzle", "shower")):
        advice.append(
            "The reported conditions suggest rain. Consider carrying "
            "an umbrella or raincoat."
        )

    if wind is not None and wind >= 35:
        advice.append(
            "Winds are strong. Be cautious around exposed areas and "
            "consider postponing activities affected by wind."
        )
    elif wind is not None and wind >= 20:
        advice.append(
            "It is breezy, so take care with exposed outdoor activities."
        )

    if humidity is not None and humidity >= 80 and temperature >= 30:
        advice.append(
            "High humidity can make warm conditions feel more uncomfortable. "
            "Take breaks in a cool place."
        )

    if "what should i wear" in question or "what to wear" in question:
        advice.insert(
            0,
            "For clothing, breathable lightweight layers are a sensible "
            "starting point in warm conditions.",
        )

    return " ".join(advice)


def generate_weather_advice(message: str, weather: dict) -> str:
    """Use Gemini when available, with a local fallback."""

    prompt = f"""
You are the weather advice specialist for AtmosIQ.

Give practical advice about clothing, umbrellas, outdoor activities,
travel, and precautions.

Rules:
- Use the supplied weather data as the source of truth.
- Never invent temperatures, rain probabilities, or wind speeds.
- If relevant data is missing, say so clearly.
- Keep the response friendly, concise, and practical.
- If the weather indicates a safety risk, prioritize safety.

Verified weather data:
{weather}

User's question:
{message}

Give a direct, useful answer.
"""

    try:
        response = get_weather_llm().invoke(prompt)
        content = response.content

        if isinstance(content, str):
            answer = content.strip()
        elif isinstance(content, list):
            answer = "\n".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ).strip()
        else:
            answer = str(content).strip() if content is not None else ""

        if answer:
            return answer

        logger.warning("Gemini returned an empty weather-advice response.")

    except Exception as exc:
        # Do not log credentials or the full provider response.
        logger.warning(
            "Gemini weather advice unavailable (%s). Using local fallback.",
            type(exc).__name__,
        )

    return generate_local_weather_advice(message, weather)

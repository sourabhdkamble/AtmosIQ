import logging

from app.agents.weather_graph_llm import get_weather_llm

logger = logging.getLogger(__name__)


def answer_weather_question_locally(message: str) -> str:
    """Answer common weather knowledge questions without an AI API."""

    question = " ".join(message.lower().split())

    answers = [
        (
            ("humidity", "humid"),
            "Humidity describes the amount of water vapour in the air. "
            "High humidity can make warm weather feel more uncomfortable "
            "because sweat evaporates less easily."
        ),
        (
            ("air pressure", "atmospheric pressure", "barometric pressure"),
            "Air pressure is the force exerted by the weight of the "
            "atmosphere. Falling pressure can accompany approaching "
            "weather systems, while rising pressure often accompanies "
            "more settled weather. It is not a guarantee."
        ),
        (
            ("why does it rain", "how does rain form", "rain formation"),
            "Rain forms when moist air rises and cools, causing water "
            "vapour to condense into cloud droplets. The droplets grow "
            "and eventually fall when they become heavy enough."
        ),
        (
            ("thunder", "lightning"),
            "Lightning is an electrical discharge in the atmosphere. "
            "Thunder is the sound produced when lightning rapidly heats "
            "the surrounding air. If you hear thunder, move indoors "
            "or into a substantial enclosed vehicle."
        ),
        (
            ("wind", "breezy"),
            "Wind is air moving from areas of higher pressure toward "
            "areas of lower pressure. Local terrain, temperature "
            "differences and larger weather systems affect its speed "
            "and direction."
        ),
        (
            ("cloud", "overcast"),
            "Clouds form when moist air cools and water vapour condenses "
            "into tiny water droplets or ice crystals. Cloud type and "
            "development can offer clues about the weather, but clouds "
            "alone cannot provide a precise forecast."
        ),
        (
            ("monsoon",),
            "A monsoon is a seasonal shift in prevailing winds that "
            "often brings a distinct wet season and dry season. In India, "
            "the southwest monsoon is a major source of seasonal rainfall."
        ),
        (
            ("heat index", "feels like", "feels-like"),
            "The 'feels like' temperature estimates how hot or cold "
            "conditions may feel to the body. Depending on the weather "
            "service, it can account for factors such as humidity, wind "
            "and solar exposure."
        ),
        (
            ("weather forecast", "forecast accuracy", "predict weather"),
            "Weather forecasts use observations and computer models "
            "to estimate future atmospheric conditions. Uncertainty "
            "generally increases further into the future, so check "
            "updated forecasts for important plans."
        ),
        (
            ("weather and climate", "difference between weather and climate"),
            "Weather describes atmospheric conditions over short "
            "periods, such as today's temperature or rain. Climate "
            "describes typical patterns and variations over much longer "
            "periods, usually decades."
        ),
    ]

    for keywords, answer in answers:
        if any(keyword in question for keyword in keywords):
            return answer

    return (
        "I can explain common weather concepts such as humidity, "
        "rain formation, wind, clouds, monsoons and forecasts. "
        "I can't reliably answer that particular question without "
        "the AI knowledge service. Please try again when it is available."
    )


def answer_weather_question(message: str) -> str:
    """Use Gemini when available, with a local knowledge fallback."""

    prompt = f"""
You are the weather knowledge specialist for AtmosIQ.

Explain general weather concepts in simple, accurate language.
Use short examples when helpful.
Distinguish established scientific facts from uncertainty.
Do not invent live weather measurements or claim to have retrieved
current weather observations.
For questions requiring live conditions or forecasts, explain that
AtmosIQ needs location-specific weather data to answer reliably.

User's question:
{message}

Provide a concise, helpful answer.
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

        logger.warning("Gemini returned an empty weather-knowledge response.")

    except Exception as exc:
        logger.warning(
            "Gemini weather knowledge unavailable (%s). Using local fallback.",
            type(exc).__name__,
        )

    return answer_weather_question_locally(message)

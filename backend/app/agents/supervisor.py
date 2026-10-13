
import json
import logging
import os
import re
from typing import Literal

from app.agents.weather_graph_llm import get_weather_llm

logger = logging.getLogger(__name__)

AgentRoute = Literal[
    "current_weather",
    "forecast",
    "weather_advice",
    "knowledge",
    "air_quality",
]

VALID_ROUTES = {
    "current_weather",
    "forecast",
    "weather_advice",
    "knowledge",
    "air_quality",
}


def route_with_keywords(message: str) -> AgentRoute:
    """Classify a request locally without an LLM call."""
    text = " ".join(message.lower().split())

    # Prioritize air-quality questions.
    if any(term in text for term in (
        "aqi", "air quality", "pollution", "polluted",
        "pm2.5", "pm10", "particulate matter",
        "particulate pollution", "air safe to breathe",
        "pollution levels", "breathing outdoor air",
    )):
        return "air_quality"

    # Advice: prioritize explicit decisions and actions.
    if any(term in text for term in (
        "what should i wear", "what should i carry",
        "what should i pack", "what should i bring",
        "what should i keep in my bag", "how should i prepare",
        "prepare for the weather", "prepare for strong winds",
        "should i take", "take a jacket", "carry a jacket",
        "what precautions", "precautions should i take",
        "raincoat", "umbrella", "footwear",
        "protect myself", "protect myself during",
        "lightweight clothes", "layers for a day",
        "commuting by motorcycle", "walk my dog",
        "outdoor workout indoors", "move my outdoor workout indoors",
        "safe to run", "outdoor exercise", "suitable for cycling",
        "good day for a picnic", "postpone a picnic",
        "should i postpone", "stay comfortable",
        "is it safe to",
    )):
        return "weather_advice"

    # Current conditions.
    if any(term in text for term in (
        "right now", "at the moment", "at this very moment",
        "currently", "at present", "present conditions",
        "current weather", "current conditions",
        "conditions outside", "weather outside",
        "weather outdoors", "like outdoors",
        "weather like", "temperature outside",
        "temperature in", "check the current weather",
        "is it raining", "how hot is it outside",
        "how cold is it outside", "how windy is it",
        "is it cloudy", "sky is clear",
        "not tomorrow's forecast",
    )):
        return "current_weather"

    # Forecast: future periods and changes over time.
    if any(term in text for term in (
        "tomorrow", "day from now", "days from now",
        "two days from now", "forecast", "next week",
        "upcoming", "hourly", "daily", "this weekend",
        "coming weekend", "next few days", "next seven days",
        "next five days", "next 24 hours", "next 48 hours",
        "48 hours", "seven-day", "seven day", "coming days",
        "outlook", "overnight", "later this evening",
        "later today", "throughout the day",
        "changes throughout the day", "over the coming",
        "what conditions are expected", "weather should i expect",
        "will rain be a concern", "will my clothes dry",
    )):
        return "forecast"

    return "knowledge"


def route_user_request(message: str) -> AgentRoute:
    """Classify with Gemini, falling back to local keyword routing.

    Set ATMOSIQ_LOCAL_ROUTING=1 to bypass Gemini.
    """
    if os.getenv("ATMOSIQ_LOCAL_ROUTING", "").strip() == "1":
        return route_with_keywords(message)

    prompt = f"""
You are the supervisor for AtmosIQ, an AI weather assistant.

Choose exactly one route:
- current_weather: conditions right now
- forecast: tomorrow or future weather
- weather_advice: what to wear, carry, or do based on weather
- knowledge: general weather concepts
- air_quality: AQI, pollution, PM2.5, or PM10

Return only JSON, for example:
{{"route": "forecast"}}

User request: {message}
"""

    try:
        response = get_weather_llm().invoke(prompt)
        content = response.content

        if isinstance(content, list):
            content = "\n".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )

        content = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            str(content),
        ).strip()

        match = re.search(r"\{.*\}", content, flags=re.DOTALL)

        if match:
            route = json.loads(match.group()).get("route")
            if route in VALID_ROUTES:
                return route

        logger.warning(
            "Supervisor returned an invalid or unparseable route; "
            "using keyword fallback."
        )

    except Exception as exc:
        logger.warning(
            "Supervisor classification failed; using keyword fallback "
            "(error_type=%s)",
            type(exc).__name__,
        )

    return route_with_keywords(message)


import json
import logging
from datetime import datetime
from typing import Literal, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from app.agents.air_quality_agent import answer_air_quality
from app.agents.supervisor import route_user_request
from app.agents.current_weather_agent import get_current_weather_for_city
from app.agents.forecast_agent import get_forecast_for_location
from app.agents.weather_advice_agent import generate_weather_advice
from app.agents.knowledge_agent import answer_weather_question
from app.agents.weather_graph_llm import get_weather_llm

logger = logging.getLogger(__name__)


class WeatherAgentState(TypedDict, total=False):
    message: str
    city: str
    intent: str
    weather: dict
    answer: str
    error: str


def normalize_model_content(content) -> str:
    """Convert common model response formats to plain text."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        return "\n".join(parts).strip()

    if content is None:
        return ""

    return str(content).strip()


def retrieve_error_message(state: WeatherAgentState) -> str:
    """Return a safe, user-friendly retrieval error."""
    return state.get("error") or (
        "I couldn't retrieve the required weather information. "
        "Please try again."
    )


async def retrieve_weather(state: WeatherAgentState) -> dict:
    """Retrieve current weather for the requested city."""
    try:
        city = state.get("city", "").strip()
        if not city:
            return {
                "weather": {},
                "error": "Please provide a city name.",
            }

        weather = await get_current_weather_for_city(city)

        if not weather:
            return {
                "weather": {},
                "error": "No current weather data was returned. Please try again.",
            }

        return {"weather": weather, "error": ""}

    except Exception:
        logger.exception("Current weather retrieval failed")
        return {
            "weather": {},
            "error": (
                "Unable to retrieve current weather. "
                "Check the city name or try again later."
            ),
        }


async def retrieve_forecast(state: WeatherAgentState) -> dict:
    """Retrieve daily or hourly forecast data."""
    message = state.get("message", "").lower()
    city = state.get("city", "").strip()

    if not city:
        return {
            "weather": {},
            "error": "Please provide a city name.",
        }

    daily_terms = (
        "tomorrow",
        "next week",
        "next few days",
        "next seven days",
        "next five days",
        "this weekend",
        "coming weekend",
        "upcoming days",
        "coming days",
        "seven-day",
        "seven day",
        "7 day",
        "7-day",
        "daily",
    )

    try:
        from app.api.weather import resolve_city

        location = await resolve_city(city)

        forecast_type = (
            "daily"
            if any(term in message for term in daily_terms)
            else "hourly"
        )

        forecast = await get_forecast_for_location(
            latitude=location["latitude"],
            longitude=location["longitude"],
            forecast_type=forecast_type,
        )

        if not forecast:
            return {
                "weather": {},
                "error": "No forecast data was returned. Please try again.",
            }

        return {
            "weather": {
                "location": location,
                "forecast": forecast,
            },
            "error": "",
        }

    except Exception:
        logger.exception("Forecast retrieval failed")
        return {
            "weather": {},
            "error": (
                "Unable to retrieve the forecast. "
                "Check the city name or try again later."
            ),
        }


def _get_rain_probability(record: dict):
    """Read supported rain-probability field names."""
    for key in (
        "precipitation_probability_max_percent",
        "precipitation_probability_percent",
        "precipitation_probability_max_pct",
        "precipitation_probability_pct",
        "precipitation_probability_max",
        "precipitation_probability",
    ):
        value = record.get(key)
        if value is None:
            continue

        try:
            probability = float(value)
            if 0 <= probability <= 100:
                return probability
        except (TypeError, ValueError):
            continue

    return None


def _format_forecast_time(value) -> str:
    """Format a provider timestamp without assuming a local timezone."""
    if not value:
        return "Date unavailable"

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if "T" in str(value):
            return parsed.strftime("%a, %d %b at %I:%M %p").replace(" 0", " ")
        return parsed.strftime("%a, %d %b")
    except (ValueError, TypeError):
        return str(value)


def _is_rain_question(message: str) -> bool:
    """Identify questions asking specifically about rain."""
    message = message.lower()
    return any(
        term in message
        for term in (
            "rain",
            "raining",
            "rainfall",
            "precipitation",
            "umbrella",
            "wet outside",
        )
    )


def _select_daily_record(records: list, message: str):
    """Select a daily record for today or tomorrow when possible."""
    if not records:
        return None

    message = message.lower()
    if "tomorrow" not in message:
        return records[0]

    target_date = datetime.now().date().toordinal() + 1

    for record in records:
        if not isinstance(record, dict):
            continue

        raw_date = record.get("date") or record.get("time")
        if not raw_date:
            continue

        try:
            parsed_date = datetime.fromisoformat(
                str(raw_date).replace("Z", "+00:00")
            ).date()

            if parsed_date.toordinal() == target_date:
                return record
        except (ValueError, TypeError):
            continue

    return records[1] if len(records) > 1 else records[0]


def _summarize_rain_question(
    weather: dict,
    message: str,
    daily_records: list,
    hourly_records: list,
) -> str:
    """Answer rain questions using actual probabilities where available."""
    location = weather.get("location", {})
    city = location.get("name", "") if isinstance(location, dict) else ""
    prefix = f"For {city}, " if city else ""
    message_lower = message.lower()

    if daily_records:
        record = _select_daily_record(daily_records, message_lower)

        if record is not None:
            probability = _get_rain_probability(record)
            description = record.get(
                "description",
                "conditions not specified",
            )
            date_value = record.get("date") or record.get("time")
            formatted_date = _format_forecast_time(date_value)

            if probability is None:
                return (
                    f"{prefix}the forecast for {formatted_date} is "
                    f"{description}, but a verified rain probability "
                    "is unavailable."
                )

            outlook = (
                "low" if probability <= 20
                else "moderate" if probability <= 50
                else "high"
            )

            return (
                f"{prefix}the rain probability for {formatted_date} "
                f"is {probability:g}% ({outlook} chance). "
                f"The forecast condition is {description}. "
                "Rain probability is an estimate, not a guarantee."
            )

    if hourly_records:
        matching_records = hourly_records

        if "tomorrow" in message_lower:
            tomorrow = datetime.now().date().toordinal() + 1
            dated_records = []

            for record in hourly_records:
                if not isinstance(record, dict):
                    continue

                raw_time = record.get("time") or record.get("date")

                try:
                    parsed = datetime.fromisoformat(
                        str(raw_time).replace("Z", "+00:00")
                    )
                    if parsed.date().toordinal() == tomorrow:
                        dated_records.append(record)
                except (ValueError, TypeError):
                    continue

            if dated_records:
                matching_records = dated_records

        probabilities = [
            _get_rain_probability(record)
            for record in matching_records
            if isinstance(record, dict)
        ]
        probabilities = [p for p in probabilities if p is not None]

        if probabilities:
            maximum = max(probabilities)
            outlook = (
                "low" if maximum <= 20
                else "moderate" if maximum <= 50
                else "high"
            )

            return (
                f"{prefix}the highest rain probability in the available "
                f"hourly forecast is {maximum:g}% ({outlook} chance). "
                "This covers only the available forecast period, "
                "not necessarily the entire day."
            )

    return (
        f"{prefix}I retrieved forecast data, but it does not contain "
        "a usable rain probability. I can't give a reliable yes/no "
        "rain prediction from the available fields."
    )


def summarize_weather_locally(
    weather: dict,
    message: str = "",
) -> str:
    """Create readable weather summaries without requiring an LLM."""
    if not isinstance(weather, dict) or not weather:
        return "Weather data is unavailable, so I can't provide a summary."

    location = weather.get("location", {})
    city = location.get("name", "") if isinstance(location, dict) else ""
    prefix = f"For {city}, " if city else ""
    forecast = weather.get("forecast")

    if isinstance(forecast, dict):
        daily_records = forecast.get("daily_forecast") or []
        hourly_records = forecast.get("hourly_forecast") or []

        if _is_rain_question(message):
            return _summarize_rain_question(
                weather,
                message,
                daily_records,
                hourly_records,
            )

        records = daily_records or hourly_records
        if not records:
            return prefix + "forecast data was retrieved, but contains no records."

        lines = [prefix + "here is the available forecast:"]

        for record in records[:5]:
            if not isinstance(record, dict):
                continue

            timestamp = record.get("time") or record.get("date")
            description = record.get("description", "Conditions not specified")
            temperature = record.get(
                "temperature_c",
                record.get("temperature"),
            )
            low = record.get(
                "temperature_min_c",
                record.get("temperature_2m_min"),
            )
            high = record.get(
                "temperature_max_c",
                record.get("temperature_2m_max"),
            )
            rain = _get_rain_probability(record)

            parts = [_format_forecast_time(timestamp), str(description)]

            if low is not None:
                parts.append(f"low {low}°C")
            if high is not None:
                parts.append(f"high {high}°C")
            if low is None and high is None and temperature is not None:
                parts.append(f"{temperature}°C")
            if rain is not None:
                parts.append(f"rain chance {rain:g}%")

            lines.append("- " + ", ".join(parts))

        return "\n".join(lines)

    parts = []
    fields = [
        ("description", "", ""),
        ("temperature_c", "temperature ", "°C"),
        ("feels_like_c", "feels like ", "°C"),
        ("humidity_percent", "humidity ", "%"),
        ("wind_speed_kmh", "wind ", " km/h"),
        ("precipitation_mm", "precipitation ", " mm"),
    ]

    for key, label, unit in fields:
        value = weather.get(key)
        if value is not None:
            parts.append(f"{label}{value}{unit}" if label else str(value))

    if not parts:
        return prefix + "weather data was retrieved, but has no recognized measurements."

    return prefix + "current conditions are " + ", ".join(parts) + "."


def answer_with_weather(state: WeatherAgentState) -> dict:
    """Explain retrieved weather, falling back to verified local summaries."""
    if state.get("error"):
        return {"answer": retrieve_error_message(state)}

    weather = state.get("weather", {})
    message = state.get("message", "")

    try:
        prompt = f"""
You are AtmosIQ, a practical weather assistant.

Answer the user's exact question directly and concisely.
For rain questions, lead with the rain probability or clearly state
when that probability is unavailable.
Use only the supplied weather data. Never invent measurements.
Distinguish current conditions from forecasts.
Do not claim a full-day forecast if only hourly data is available.

Verified weather data:
{json.dumps(weather, ensure_ascii=False, default=str)}

User's question:
{message}
"""
        response = get_weather_llm().invoke(prompt)
        answer = normalize_model_content(response.content)

        if answer:
            return {"answer": answer}

    except Exception as exc:
        logger.warning(
            "Gemini weather summary unavailable (%s). Using local summary.",
            type(exc).__name__,
        )

    return {"answer": summarize_weather_locally(weather, message)}


def answer_weather_advice(state: WeatherAgentState) -> dict:
    """Generate practical advice grounded in retrieved weather."""
    if state.get("error"):
        return {"answer": retrieve_error_message(state)}

    try:
        answer = generate_weather_advice(
            message=state.get("message", ""),
            weather=state.get("weather", {}),
        )

        if not answer or not answer.strip():
            return {
                "answer": (
                    "I couldn't generate weather advice right now. "
                    "Please try again."
                )
            }

        return {"answer": answer.strip()}

    except Exception:
        logger.exception("Weather advice agent failed")
        return {
            "answer": (
                "I couldn't generate weather advice right now. "
                "Please try again."
            )
        }


def answer_knowledge(state: WeatherAgentState) -> dict:
    """Delegate general weather questions to the knowledge specialist."""
    try:
        answer = answer_weather_question(state.get("message", ""))

        if not answer or not answer.strip():
            return {
                "answer": (
                    "I couldn't generate an explanation right now. "
                    "Please try again."
                )
            }

        return {"answer": answer.strip()}

    except Exception:
        logger.exception("Weather knowledge agent failed")
        return {
            "answer": (
                "The weather knowledge service is temporarily unavailable. "
                "Please try again."
            )
        }


def classify_request(state: WeatherAgentState) -> dict:
    """Ask the supervisor to classify the request."""
    return {"intent": route_user_request(state.get("message", ""))}


def choose_route(
    state: WeatherAgentState,
) -> Literal[
    "retrieve_weather",
    "retrieve_forecast",
    "answer_knowledge",
    "answer_air_quality",
]:
    """Choose the graph branch for the classified intent."""
    intent = state.get("intent")

    if intent == "forecast":
        return "retrieve_forecast"

    if intent in {"current_weather", "weather_advice"}:
        return "retrieve_weather"

    if intent == "air_quality":
        return "answer_air_quality"

    return "answer_knowledge"


def choose_weather_response(
    state: WeatherAgentState,
) -> Literal["answer_weather_advice", "answer_with_weather"]:
    if state.get("intent") == "weather_advice":
        return "answer_weather_advice"

    return "answer_with_weather"


def build_weather_graph():
    """Build the AtmosIQ supervisor and specialist workflow."""
    graph_builder = StateGraph(WeatherAgentState)

    graph_builder.add_node("supervisor", classify_request)
    graph_builder.add_node("retrieve_weather", retrieve_weather)
    graph_builder.add_node("retrieve_forecast", retrieve_forecast)
    graph_builder.add_node("answer_with_weather", answer_with_weather)
    graph_builder.add_node("answer_weather_advice", answer_weather_advice)
    graph_builder.add_node("answer_knowledge", answer_knowledge)
    graph_builder.add_node("answer_air_quality", answer_air_quality)

    graph_builder.add_edge(START, "supervisor")

    graph_builder.add_conditional_edges(
        "supervisor",
        choose_route,
        {
            "retrieve_weather": "retrieve_weather",
            "retrieve_forecast": "retrieve_forecast",
            "answer_knowledge": "answer_knowledge",
            "answer_air_quality": "answer_air_quality",
        },
    )

    graph_builder.add_conditional_edges(
        "retrieve_weather",
        choose_weather_response,
        {
            "answer_weather_advice": "answer_weather_advice",
            "answer_with_weather": "answer_with_weather",
        },
    )

    graph_builder.add_edge("retrieve_forecast", "answer_with_weather")
    graph_builder.add_edge("answer_with_weather", END)
    graph_builder.add_edge("answer_weather_advice", END)
    graph_builder.add_edge("answer_knowledge", END)
    graph_builder.add_edge("answer_air_quality", END)

    return graph_builder.compile()


weather_graph = build_weather_graph()

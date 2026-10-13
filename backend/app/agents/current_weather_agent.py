
from app.api.weather import add_current_interpretation, resolve_city
from app.tools.weather_api import get_current_weather


async def get_current_weather_for_city(city: str) -> dict:
    """Retrieve current weather and add human-readable interpretation."""

    location = await resolve_city(city)

    current = await get_current_weather(
        location["latitude"],
        location["longitude"],
    )

    weather = add_current_interpretation(current)
    weather["location"] = location

    return weather

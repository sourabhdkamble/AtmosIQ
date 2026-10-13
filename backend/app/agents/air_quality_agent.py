
"""Air quality specialist for AtmosIQ."""

import logging

import httpx

from app.services.air_quality_api import get_current_air_quality
from app.tools.weather_api import geocode_location

logger = logging.getLogger(__name__)


async def get_air_quality_for_city(city: str) -> dict:
    """Retrieve live air-quality data for a city."""
    city = city.strip()
    if not city:
        raise ValueError("City must not be empty.")

    location = await geocode_location(city)

    air_quality = await get_current_air_quality(
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=location.get("timezone") or "auto",
    )

    return {
        "location": location,
        "air_quality": air_quality,
    }


async def answer_air_quality(state: dict) -> dict:
    """Return verified provider readings or a safe error response."""
    city = state.get("city", "")

    try:
        result = await get_air_quality_for_city(city)

        location = result["location"]
        data = result["air_quality"]
        city_name = location.get("name") or city

        aqi = data.get("us_aqi")
        pm25 = data.get("pm2_5_ug_m3")
        pm10 = data.get("pm10_ug_m3")
        timestamp = data.get("time")

        details = []
        if aqi is not None:
            details.append(f"US AQI: {aqi}")
        if pm25 is not None:
            details.append(f"PM2.5: {pm25} µg/m³")
        if pm10 is not None:
            details.append(f"PM10: {pm10} µg/m³")

        if not details:
            return {
                "answer": (
                    f"Air-quality data for {city_name} was returned, "
                    "but it contains no usable AQI or particulate readings."
                ),
                "weather": {},
            }

        answer = (
            f"Current air-quality data for {city_name}: "
            + "; ".join(details)
            + "."
        )

        if timestamp:
            answer += f" Provider observation time: {timestamp}."
        answer += (
            " Source: Open-Meteo Air Quality API. "
            "US AQI is not the Indian CPCB AQI."
        )

        return {
            "answer": answer,
            "weather": result,
        }

    except ValueError:
        logger.warning("Invalid or missing air-quality data for city %r", city)
        return {
            "answer": (
                "I couldn't obtain usable air-quality data for that city. "
                "Please check the city name and try again."
            ),
            "weather": {},
        }

    except (httpx.HTTPError, LookupError):
        logger.exception("Air-quality provider request failed")
        return {
            "answer": (
                "Live air-quality data is temporarily unavailable. "
                "Please try again later."
            ),
            "weather": {},
        }

    except Exception:
        logger.exception("Unexpected air-quality agent failure")
        return {
            "answer": (
                "I couldn't retrieve air-quality data right now. "
                "Please try again later."
            ),
            "weather": {},
        }

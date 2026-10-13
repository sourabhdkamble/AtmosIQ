
import httpx
from fastapi import APIRouter, HTTPException, Query

from app.tools.weather_api import (
    geocode_location,
    get_current_weather,
    get_daily_forecast,
    get_hourly_forecast,
)
from app.services.weather_interpreter import (
    describe_weather_code,
    generate_weather_advice,
)

router = APIRouter(prefix="/api/v1/weather", tags=["Weather"])


async def resolve_city(city: str) -> dict:
    try:
        return await geocode_location(city)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Geocoding timed out."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail="Geocoding provider error."
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach geocoding provider.",
        ) from exc


def add_current_interpretation(current: dict) -> dict:
    """Add a readable description and practical advice."""

    result = current.copy()
    result["description"] = describe_weather_code(
        current.get("weather_code")
    )
    result["advice"] = generate_weather_advice(
        temperature_c=current.get("temperature_c"),
        wind_speed_kmh=current.get("wind_speed_kmh"),
        weather_code=current.get("weather_code"),
    )
    return result


def add_forecast_interpretation(record: dict) -> dict:
    """Add a readable description to an hourly or daily record."""

    result = record.copy()
    result["description"] = describe_weather_code(
        record.get("weather_code")
    )
    return result


@router.get("")
async def current_weather(
    city: str = Query(..., min_length=1, max_length=100),
):
    location = await resolve_city(city)

    try:
        current = await get_current_weather(
            location["latitude"],
            location["longitude"],
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Weather request timed out."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail="Weather provider error."
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach weather provider.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "location": location,
        "current_weather": add_current_interpretation(current),
        "source": "Open-Meteo",
    }


@router.get("/hourly")
async def hourly_weather(
    city: str = Query(..., min_length=1, max_length=100),
    hours: int = Query(24, ge=1, le=48),
):
    location = await resolve_city(city)

    try:
        forecast = await get_hourly_forecast(
            location["latitude"],
            location["longitude"],
            hours,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Hourly forecast timed out."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail="Weather provider error."
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach weather provider.",
        ) from exc

    forecast["hourly_forecast"] = [
        add_forecast_interpretation(record)
        for record in forecast["hourly_forecast"]
    ]

    return {"location": location, **forecast}


@router.get("/daily")
async def daily_weather(
    city: str = Query(..., min_length=1, max_length=100),
    days: int = Query(7, ge=1, le=16),
):
    location = await resolve_city(city)

    try:
        forecast = await get_daily_forecast(
            location["latitude"],
            location["longitude"],
            days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Daily forecast timed out."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail="Weather provider error."
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach weather provider.",
        ) from exc

    forecast["daily_forecast"] = [
        add_forecast_interpretation(record)
        for record in forecast["daily_forecast"]
    ]

    return {"location": location, **forecast}

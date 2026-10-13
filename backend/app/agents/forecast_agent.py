
from app.services.weather_interpreter import describe_weather_code
from app.tools.weather_api import (
    get_daily_forecast,
    get_hourly_forecast,
)


async def get_forecast_for_location(
    latitude: float,
    longitude: float,
    forecast_type: str = "hourly",
) -> dict:
    """Retrieve and interpret hourly or daily forecast data."""

    if forecast_type == "daily":
        forecast = await get_daily_forecast(
            latitude,
            longitude,
            7,
        )
        forecast_key = "daily_forecast"
    elif forecast_type == "hourly":
        forecast = await get_hourly_forecast(
            latitude,
            longitude,
            24,
        )
        forecast_key = "hourly_forecast"
    else:
        raise ValueError(
            "forecast_type must be 'hourly' or 'daily'."
        )

    records = forecast.get(forecast_key, [])
    interpreted_records = []

    for record in records:
        item = record.copy()
        item["description"] = describe_weather_code(
            item.get("weather_code")
        )
        interpreted_records.append(item)

    forecast[forecast_key] = interpreted_records

    return forecast

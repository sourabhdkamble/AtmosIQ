
import httpx


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT_SECONDS = 15.0


async def geocode_location(city: str) -> dict:
    """Resolve a city name to geographic coordinates."""

    city = city.strip()
    if not city:
        raise ValueError("City name cannot be empty.")

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            GEOCODING_URL,
            params={
                "name": city,
                "count": 5,
                "language": "en",
                "format": "json",
            },
        )
        response.raise_for_status()
        data = response.json()

    results = data.get("results", [])
    if not results:
        raise LookupError(f"No location found for '{city}'.")

    # India-first assistant: if multiple matches exist, prioritize India
    indian_matches = [
        r for r in results
        if r.get("country_code", "").upper() == "IN"
        or str(r.get("country", "")).strip().lower() == "india"
    ]
    location = indian_matches[0] if indian_matches else results[0]

    return {
        "name": location["name"],
        "country": location.get("country"),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location.get("timezone"),
    }


async def get_current_weather(latitude: float, longitude: float) -> dict:
    """Fetch current weather conditions."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,is_day,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        data = response.json()

    current = data.get("current")
    if not current:
        raise ValueError("The provider returned no current conditions.")

    return {
        "time": current.get("time"),
        "temperature_c": current.get("temperature_2m"),
        "feels_like_c": current.get("apparent_temperature"),
        "humidity_percent": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "precipitation_mm": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "is_day": current.get("is_day"),
    }


async def get_weather_by_city(city: str) -> dict:
    """Return current weather for a city."""

    location = await geocode_location(city)

    current_weather = await get_current_weather(
        location["latitude"],
        location["longitude"],
    )

    return {
        "location": location,
        "current_weather": current_weather,
        "source": "Open-Meteo",
        "units": {
            "temperature": "°C",
            "wind_speed": "km/h",
            "precipitation": "mm",
        },
    }


async def get_hourly_forecast(
    latitude: float,
    longitude: float,
    forecast_hours: int = 24,
) -> dict:
    """Fetch hourly weather forecasts."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")
    if not 1 <= forecast_hours <= 48:
        raise ValueError("forecast_hours must be between 1 and 48.")

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": (
                    "temperature_2m,relative_humidity_2m,"
                    "precipitation_probability,precipitation,"
                    "wind_speed_10m,weather_code"
                ),
                "forecast_hours": forecast_hours,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        data = response.json()

    hourly = data.get("hourly")
    if not hourly or "time" not in hourly:
        raise ValueError("The provider returned no hourly forecast.")

    fields = {
        "temperature_c": "temperature_2m",
        "humidity_percent": "relative_humidity_2m",
        "precipitation_probability_percent": "precipitation_probability",
        "precipitation_mm": "precipitation",
        "wind_speed_kmh": "wind_speed_10m",
        "weather_code": "weather_code",
    }

    forecasts = []

    for index, timestamp in enumerate(hourly["time"]):
        record = {"time": timestamp}

        for output_name, api_name in fields.items():
            values = hourly.get(api_name, [])
            record[output_name] = (
                values[index] if index < len(values) else None
            )

        forecasts.append(record)

    return {
        "timezone": data.get("timezone"),
        "forecast_hours": len(forecasts),
        "hourly_forecast": forecasts,
        "source": "Open-Meteo",
        "units": {
            "temperature": "°C",
            "wind_speed": "km/h",
            "precipitation": "mm",
        },
    }


async def get_daily_forecast(
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
) -> dict:
    """Fetch daily weather forecasts."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")
    if not 1 <= forecast_days <= 16:
        raise ValueError("forecast_days must be between 1 and 16.")

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.get(
            FORECAST_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,sunrise,sunset,"
                    "precipitation_probability_max,"
                    "precipitation_sum,wind_speed_10m_max"
                ),
                "forecast_days": forecast_days,
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        data = response.json()

    daily = data.get("daily")
    if not daily or "time" not in daily:
        raise ValueError("The provider returned no daily forecast.")

    fields = {
        "weather_code": "weather_code",
        "temperature_max_c": "temperature_2m_max",
        "temperature_min_c": "temperature_2m_min",
        "sunrise": "sunrise",
        "sunset": "sunset",
        "precipitation_probability_max_percent": (
            "precipitation_probability_max"
        ),
        "precipitation_sum_mm": "precipitation_sum",
        "wind_speed_max_kmh": "wind_speed_10m_max",
    }

    forecasts = []

    for index, date in enumerate(daily["time"]):
        record = {"date": date}

        for output_name, api_name in fields.items():
            values = daily.get(api_name, [])
            record[output_name] = (
                values[index] if index < len(values) else None
            )

        forecasts.append(record)

    return {
        "timezone": data.get("timezone"),
        "forecast_days": len(forecasts),
        "daily_forecast": forecasts,
        "source": "Open-Meteo",
        "units": {
            "temperature": "°C",
            "wind_speed": "km/h",
            "precipitation": "mm",
        },
    }

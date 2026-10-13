
def describe_weather_code(code: int | None) -> str:
    """Convert a WMO weather code into a readable description."""

    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    if code is None:
        return "Weather conditions unavailable"

    return descriptions.get(code, "Unknown weather conditions")


def generate_weather_advice(
    temperature_c: float | None,
    precipitation_probability_percent: float | None = None,
    wind_speed_kmh: float | None = None,
    weather_code: int | None = None,
) -> list[str]:
    """Generate practical advice from available weather data."""

    advice = []

    if temperature_c is not None:
        if temperature_c >= 35:
            advice.append(
                "Very hot conditions: limit strenuous outdoor activity "
                "and drink water regularly."
            )
        elif temperature_c >= 30:
            advice.append(
                "Warm conditions: stay hydrated, especially outdoors."
            )
        elif temperature_c <= 5:
            advice.append(
                "Very cold conditions: wear warm clothing outdoors."
            )

    if precipitation_probability_percent is not None:
        if precipitation_probability_percent >= 70:
            advice.append(
                "High chance of precipitation: carry suitable rain gear."
            )
        elif precipitation_probability_percent >= 40:
            advice.append(
                "There is a chance of precipitation: check the forecast "
                "before heading out."
            )

    if wind_speed_kmh is not None and wind_speed_kmh >= 40:
        advice.append(
            "Strong winds are possible: take care around exposed areas "
            "and loose outdoor objects."
        )

    if weather_code is not None:
        if weather_code >= 95:
            advice.append(
                "Thunderstorm conditions: seek shelter and avoid exposed "
                "outdoor areas."
            )
        elif weather_code in {
            51, 53, 55, 56, 57,
            61, 63, 65, 66, 67,
            80, 81, 82,
        }:
            advice.append(
                "Rain or drizzle is occurring or expected: consider "
                "carrying an umbrella."
            )
        elif weather_code in {71, 73, 75, 77, 85, 86}:
            advice.append(
                "Snow or snow showers are possible: dress appropriately "
                "and take care when travelling."
            )
        elif weather_code in {45, 48}:
            advice.append(
                "Fog may reduce visibility: take extra care when travelling."
            )

    if not advice:
        advice.append(
            "No special precautions identified from the available data."
        )

    return advice

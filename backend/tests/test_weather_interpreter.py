
from app.services.weather_interpreter import (
    describe_weather_code,
    generate_weather_advice,
)


def test_clear_sky_description():
    assert describe_weather_code(0) == "Clear sky"


def test_unknown_weather_code():
    assert (
        describe_weather_code(999)
        == "Unknown weather conditions"
    )


def test_missing_weather_code():
    assert (
        describe_weather_code(None)
        == "Weather conditions unavailable"
    )


def test_hot_weather_advice():
    advice = generate_weather_advice(36)

    assert any("Very hot" in item for item in advice)


def test_high_rain_probability_advice():
    advice = generate_weather_advice(
        temperature_c=25,
        precipitation_probability_percent=80,
    )

    assert any("High chance" in item for item in advice)


def test_thunderstorm_advice():
    advice = generate_weather_advice(
        temperature_c=25,
        weather_code=95,
    )

    assert any("Thunderstorm" in item for item in advice)


def test_rain_weather_advice():
    advice = generate_weather_advice(
        temperature_c=25,
        weather_code=61,
    )

    assert any("umbrella" in item for item in advice)


def test_fog_weather_advice():
    advice = generate_weather_advice(
        temperature_c=20,
        weather_code=45,
    )

    assert any("visibility" in item for item in advice)

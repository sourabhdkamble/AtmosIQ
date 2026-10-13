import httpx
import pytest

from app.agents import air_quality_agent


@pytest.mark.asyncio
async def test_answer_air_quality_success(monkeypatch):
    async def fake_get_air_quality_for_city(city):
        assert city == "Mumbai"
        return {
            "location": {"name": "Mumbai"},
            "air_quality": {
                "us_aqi": 72,
                "pm2_5_ug_m3": 18.5,
                "pm10_ug_m3": 32.0,
                "time": "2026-10-12T12:00",
            },
        }

    monkeypatch.setattr(
        air_quality_agent,
        "get_air_quality_for_city",
        fake_get_air_quality_for_city,
    )

    result = await air_quality_agent.answer_air_quality(
        {"city": "Mumbai"}
    )

    assert "Mumbai" in result["answer"]
    assert "US AQI: 72" in result["answer"]
    assert "PM2.5: 18.5" in result["answer"]
    assert "PM10: 32.0" in result["answer"]
    assert "Open-Meteo Air Quality API" in result["answer"]
    assert "not the Indian CPCB AQI" in result["answer"]
    assert result["weather"]["air_quality"]["us_aqi"] == 72


@pytest.mark.asyncio
async def test_answer_air_quality_with_no_usable_readings(monkeypatch):
    async def fake_get_air_quality_for_city(city):
        return {
            "location": {"name": "Mumbai"},
            "air_quality": {
                "us_aqi": None,
                "pm2_5_ug_m3": None,
                "pm10_ug_m3": None,
            },
        }

    monkeypatch.setattr(
        air_quality_agent,
        "get_air_quality_for_city",
        fake_get_air_quality_for_city,
    )

    result = await air_quality_agent.answer_air_quality(
        {"city": "Mumbai"}
    )

    assert "no usable AQI or particulate readings" in result["answer"]
    assert result["weather"] == {}


@pytest.mark.asyncio
async def test_answer_air_quality_handles_value_error(monkeypatch):
    async def fake_get_air_quality_for_city(city):
        raise ValueError("Invalid city or missing data")

    monkeypatch.setattr(
        air_quality_agent,
        "get_air_quality_for_city",
        fake_get_air_quality_for_city,
    )

    result = await air_quality_agent.answer_air_quality(
        {"city": "Unknown"}
    )

    assert "check the city name" in result["answer"]
    assert result["weather"] == {}


@pytest.mark.asyncio
async def test_answer_air_quality_handles_http_error(monkeypatch):
    async def fake_get_air_quality_for_city(city):
        request = httpx.Request(
            "GET",
            "https://air-quality-api.open-meteo.com/v1/air-quality",
        )
        response = httpx.Response(503, request=request)
        raise httpx.HTTPStatusError(
            "Provider unavailable",
            request=request,
            response=response,
        )

    monkeypatch.setattr(
        air_quality_agent,
        "get_air_quality_for_city",
        fake_get_air_quality_for_city,
    )

    result = await air_quality_agent.answer_air_quality(
        {"city": "Mumbai"}
    )

    assert "temporarily unavailable" in result["answer"]
    assert result["weather"] == {}

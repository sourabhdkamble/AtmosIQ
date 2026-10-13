import pytest

from app.agents import weather_graph as graph_module


@pytest.mark.asyncio
async def test_chat_graph_routes_aqi_request_to_air_quality_agent(monkeypatch):
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

    monkeypatch.setenv("ATMOSIQ_LOCAL_ROUTING", "1")
    monkeypatch.setattr(
        graph_module,
        "answer_air_quality",
        graph_module.answer_air_quality,
    )

    from app.agents import air_quality_agent

    monkeypatch.setattr(
        air_quality_agent,
        "get_air_quality_for_city",
        fake_get_air_quality_for_city,
    )

    result = await graph_module.weather_graph.ainvoke(
        {
            "message": "What is the current AQI in Mumbai?",
            "city": "Mumbai",
        }
    )

    assert result["intent"] == "air_quality"
    assert "US AQI: 72" in result["answer"]
    assert "PM2.5: 18.5" in result["answer"]
    assert "PM10: 32.0" in result["answer"]
    assert "not the Indian CPCB AQI" in result["answer"]

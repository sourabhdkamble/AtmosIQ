import pytest
from unittest.mock import AsyncMock, patch
import httpx
from httpx import ASGITransport, AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_scenario_1_current_temp_mumbai():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.api.weather.geocode_location", new_callable=AsyncMock) as m_geo, \
             patch("app.api.weather.get_current_weather", new_callable=AsyncMock) as m_w:
            m_geo.return_value = {"name": "Mumbai", "country": "India", "latitude": 19.07, "longitude": 72.87, "timezone": "Asia/Kolkata"}
            m_w.return_value = {"time": "2026-10-12T12:00", "temperature_c": 33.4, "feels_like_c": 39.1, "humidity_percent": 70, "wind_speed_kmh": 12.0, "precipitation_mm": 0.0, "weather_code": 0, "is_day": 1}
            resp = await client.get("/api/v1/weather?city=Mumbai")
            assert resp.status_code == 200
            assert resp.json()["current_weather"]["temperature_c"] == 33.4


@pytest.mark.asyncio
async def test_scenario_2_tomorrow_forecast_mumbai():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "Tomorrow's forecast in Mumbai"})
        assert resp.status_code == 200
        assert "answer" in resp.json()


@pytest.mark.asyncio
async def test_scenario_3_rain_probability():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "What is the rain probability tomorrow in Mumbai?"})
        assert resp.status_code == 200
        assert any(w in resp.json()["answer"].lower() for w in ["rain", "chance", "probability"])


@pytest.mark.asyncio
async def test_scenario_4_hourly_forecast_24h():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.api.weather.geocode_location", new_callable=AsyncMock) as m_geo, \
             patch("app.api.weather.get_hourly_forecast", new_callable=AsyncMock) as m_h:
            m_geo.return_value = {"name": "Mumbai", "country": "India", "latitude": 19.07, "longitude": 72.87, "timezone": "Asia/Kolkata"}
            m_h.return_value = {
                "timezone": "Asia/Kolkata", "forecast_hours": 24,
                "hourly_forecast": [{"time": f"2026-10-12T{h:02d}:00", "temperature_c": 30.0, "weather_code": 1} for h in range(24)],
                "source": "Open-Meteo"
            }
            resp = await client.get("/api/v1/weather/hourly?city=Mumbai&hours=24")
            assert resp.status_code == 200
            assert len(resp.json()["hourly_forecast"]) == 24


@pytest.mark.asyncio
async def test_scenario_5_daily_forecast_7d():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.api.weather.geocode_location", new_callable=AsyncMock) as m_geo, \
             patch("app.api.weather.get_daily_forecast", new_callable=AsyncMock) as m_d:
            m_geo.return_value = {"name": "Mumbai", "country": "India", "latitude": 19.07, "longitude": 72.87, "timezone": "Asia/Kolkata"}
            m_d.return_value = {
                "timezone": "Asia/Kolkata", "forecast_days": 7,
                "daily_forecast": [{"date": f"2026-10-{12+d}", "weather_code": 1, "temperature_max_c": 34.0, "temperature_min_c": 26.0} for d in range(7)],
                "source": "Open-Meteo"
            }
            resp = await client.get("/api/v1/weather/daily?city=Mumbai&days=7")
            assert resp.status_code == 200
            assert len(resp.json()["daily_forecast"]) == 7


@pytest.mark.asyncio
async def test_scenario_6_clothing_advice():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "What should I wear today in Mumbai?"})
        assert resp.status_code == 200
        assert any(w in resp.json()["answer"].lower() for w in ["wear", "clothing", "layers", "comfortable", "lightweight"])


@pytest.mark.asyncio
async def test_scenario_7_running_outdoors():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "Is it safe to run outdoors in Mumbai right now?"})
        assert resp.status_code == 200
        assert len(resp.json()["answer"]) > 10


@pytest.mark.asyncio
async def test_scenario_8_humidity_heat():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "How does high humidity affect perceived heat?"})
        assert resp.status_code == 200
        assert "humidity" in resp.json()["answer"].lower()


@pytest.mark.asyncio
async def test_scenario_9_severe_weather():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.agents.weather_graph.get_current_weather_for_city", new_callable=AsyncMock) as m_c:
            m_c.return_value = {
                "temperature_c": 24.0, "feels_like_c": 24.0, "humidity_percent": 95, "wind_speed_kmh": 45.0,
                "precipitation_mm": 25.0, "weather_code": 95, "description": "Thunderstorm",
                "location": {"name": "Mumbai", "country": "India"}
            }
            resp = await client.post("/api/v1/chat", json={"city": "Mumbai", "message": "What precautions should I take in Mumbai right now?"})
            assert resp.status_code == 200
            assert any(w in resp.json()["answer"].lower() for w in ["precipitation", "thunderstorm", "wind", "umbrella", "conditions"])


@pytest.mark.asyncio
async def test_scenario_11_unsupported_location():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/api/v1/weather?city=ZzZqQxY_12345_InvalidLocation")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_scenario_12_timeout_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.api.weather.geocode_location", new_callable=AsyncMock) as m_geo:
            m_geo.side_effect = httpx.TimeoutException("Upstream timeout")
            resp = await client.get("/api/v1/weather?city=Delhi")
            assert resp.status_code == 504


@pytest.mark.asyncio
async def test_scenario_13_empty_provider_response():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        with patch("app.api.weather.geocode_location", new_callable=AsyncMock) as m_geo, \
             patch("app.api.weather.get_current_weather", new_callable=AsyncMock) as m_w:
            m_geo.return_value = {"name": "Delhi", "latitude": 28.61, "longitude": 77.20}
            m_w.side_effect = ValueError("The provider returned no current conditions.")
            resp = await client.get("/api/v1/weather?city=Delhi")
            assert resp.status_code == 502


@pytest.mark.asyncio
async def test_scenario_14_science_question():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Pune", "message": "What is relative humidity?"})
        assert resp.status_code == 200
        assert "humidity" in resp.json()["answer"].lower()


@pytest.mark.asyncio
async def test_scenario_15_combined_weather_advice():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.post("/api/v1/chat", json={"city": "Bengaluru", "message": "Check current weather in Bengaluru and tell me what to wear"})
        assert resp.status_code == 200
        assert len(resp.json()["answer"]) > 10

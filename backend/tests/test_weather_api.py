
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tools.weather_api import (
    geocode_location,
    get_hourly_forecast,
    get_daily_forecast,
)


@pytest.mark.asyncio
async def test_geocode_rejects_empty_city():
    with pytest.raises(ValueError, match="cannot be empty"):
        await geocode_location("   ")


@pytest.mark.asyncio
async def test_hourly_forecast_rejects_invalid_hours():
    with pytest.raises(ValueError, match="forecast_hours"):
        await get_hourly_forecast(18.9, 73.1, 0)


@pytest.mark.asyncio
async def test_daily_forecast_rejects_invalid_days():
    with pytest.raises(ValueError, match="forecast_days"):
        await get_daily_forecast(18.9, 73.1, 0)


@pytest.mark.asyncio
async def test_geocode_returns_location():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "Panvel",
                "country": "India",
                "latitude": 18.98878,
                "longitude": 73.11013,
                "timezone": "Asia/Kolkata",
            }
        ]
    }
    mock_response.raise_for_status.return_value = None

    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__ = AsyncMock(
        return_value=mock_client_instance
    )
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)
    mock_client_instance.get = AsyncMock(return_value=mock_response)

    with patch(
        "app.tools.weather_api.httpx.AsyncClient",
        return_value=mock_client_instance,
    ):
        result = await geocode_location("Panvel")

    assert result["name"] == "Panvel"
    assert result["country"] == "India"
    assert result["latitude"] == 18.98878
    assert result["longitude"] == 73.11013

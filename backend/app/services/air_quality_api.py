
import httpx


AIR_QUALITY_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)
TIMEOUT_SECONDS = 15.0


async def get_current_air_quality(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
) -> dict:
    """Fetch current air-quality conditions for geographic coordinates."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    variables = (
        "european_aqi,us_aqi,pm2_5,pm10,"
        "nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide"
    )

    async with httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS
    ) as client:
        response = await client.get(
            AIR_QUALITY_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": variables,
                "timezone": timezone,
            },
        )
        response.raise_for_status()
        data = response.json()

    current = data.get("current")

    if not current:
        raise ValueError(
            "The provider returned no current air-quality data."
        )

    return {
        "time": current.get("time"),
        "european_aqi": current.get("european_aqi"),
        "us_aqi": current.get("us_aqi"),
        "pm2_5_ug_m3": current.get("pm2_5"),
        "pm10_ug_m3": current.get("pm10"),
        "nitrogen_dioxide_ug_m3": current.get("nitrogen_dioxide"),
        "ozone_ug_m3": current.get("ozone"),
        "sulphur_dioxide_ug_m3": current.get("sulphur_dioxide"),
        "carbon_monoxide_ug_m3": current.get("carbon_monoxide"),
        "timezone": data.get("timezone"),
        "source": "Open-Meteo Air Quality API",
    }


import httpx
from fastapi import APIRouter, HTTPException, Query

from app.tools.weather_api import geocode_location
from app.services.air_quality_api import get_current_air_quality

router = APIRouter(
    prefix="/api/v1/air-quality",
    tags=["Air Quality"],
)


@router.get("")
async def current_air_quality(
    city: str = Query(..., min_length=1, max_length=100),
):
    try:
        location = await geocode_location(city)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Location lookup timed out.",
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Geocoding provider error.",
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach geocoding provider.",
        ) from exc

    try:
        air_quality = await get_current_air_quality(
            latitude=location["latitude"],
            longitude=location["longitude"],
            timezone=location.get("timezone") or "auto",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Air-quality request timed out.",
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail="Air-quality provider error.",
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to reach air-quality provider.",
        ) from exc

    return {
        "location": location,
        "air_quality": air_quality,
    }

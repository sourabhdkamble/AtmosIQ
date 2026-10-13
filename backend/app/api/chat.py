import asyncio
import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.weather_graph import weather_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    city: str = Field(min_length=1, max_length=100)


class ChatResponse(BaseModel):
    city: str
    answer: str
    weather: dict


@router.post("", response_model=ChatResponse)
async def chat_with_weather_assistant(request: ChatRequest):
    try:
        result = await weather_graph.ainvoke({
            "message": request.message.strip(),
            "city": request.city.strip(),
        })

    except httpx.TimeoutException as exc:
        logger.warning("The weather provider timed out during chat execution")
        raise HTTPException(
            status_code=504,
            detail="The weather provider timed out.",
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "The weather provider returned an HTTP error during chat (status=%s)",
            getattr(exc.response, "status_code", "unknown"),
        )
        raise HTTPException(
            status_code=502,
            detail="The weather provider returned an error.",
        ) from exc
    except httpx.RequestError as exc:
        logger.warning(
            "Unable to reach the weather provider during chat (%s)",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to reach the weather provider.",
        ) from exc
    except Exception as exc:
        logger.error(
            "The AtmosIQ agent workflow failed during chat (error_type=%s)",
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=502,
            detail="The AtmosIQ agent workflow failed.",
        ) from exc

    weather = result.get("weather") or {}
    location = weather.get("location", {})

    return {
        "city": location.get("name", request.city.strip()),
        "answer": result.get(
            "answer",
            "Sorry, I couldn't generate a response.",
        ),
        "weather": weather,
    }

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.air_quality import router as air_quality_router
from app.api.chat import router as chat_router
from app.api.weather import router as weather_router

# Configure application-wide console logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AtmosIQ Weather API",
    description="Weather forecasts and an AI-powered conversational weather assistant.",
    version="0.5.0",
)

# Configure Cross-Origin Resource Sharing (CORS) for development and frontend clients.
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ATMOSIQ_CORS_ORIGINS",
        "http://localhost:8501,http://127.0.0.1:8501,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers.
app.include_router(weather_router)
app.include_router(chat_router)
app.include_router(air_quality_router)


@app.get("/")
async def root():
    return {
        "app": "AtmosIQ",
        "message": "Weather bot is running!",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "atmosiq-weather-backend",
    }
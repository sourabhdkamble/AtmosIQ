
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


@lru_cache(maxsize=1)
def get_weather_llm() -> ChatGoogleGenerativeAI:
    gemini_enabled = (
        os.getenv("ATMOSIQ_USE_GEMINI", "true").strip().lower()
        in {"1", "true", "yes", "on"}
    )

    if not gemini_enabled:
        raise RuntimeError(
            "Gemini is temporarily disabled by ATMOSIQ_USE_GEMINI."
        )

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Check backend/.env."
        )

    model_name = os.getenv("ATMOSIQ_GEMINI_MODEL", "gemini-1.5-flash").strip()
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0,
    )

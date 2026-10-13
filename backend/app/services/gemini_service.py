
import os

from dotenv import load_dotenv
from google import genai

# Load environment variables from backend/.env
load_dotenv()

MODEL_NAME = os.getenv("ATMOSIQ_GEMINI_MODEL", "gemini-1.5-flash").strip()


def generate_ai_response(prompt: str) -> str:
    """Generate a response using the configured Gemini model."""

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing from the environment."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    answer = response.text

    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    return answer.strip()

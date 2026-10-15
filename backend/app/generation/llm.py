
import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai

load_dotenv()


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to backend/.env."
        )

    return genai.Client(api_key=api_key)


def generate_text(
    prompt: str,
    temperature: float = 0.2,
    max_output_tokens: int = 1024,
) -> str:
    """Generate text using the configured Gemini model."""
    if not prompt or not prompt.strip():
        raise ValueError("prompt must not be empty")

    if not 0 <= temperature <= 2:
        raise ValueError("temperature must be between 0 and 2")

    if max_output_tokens < 1:
        raise ValueError("max_output_tokens must be at least 1")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    response = get_gemini_client().models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text.strip()

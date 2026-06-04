from typing import Any

from .base import LLMProvider
from .openai_provider import OpenAIProvider


def create_provider(settings: dict[str, Any]) -> LLMProvider:
    """Create a provider based on configuration settings."""
    provider_type = settings.get("provider", "").lower()

    if provider_type == "openai-compatible":
        return OpenAIProvider(
            base_url=settings["base_url"],
            api_key=settings["api_key"],
            model_name=settings["model_name"],
            temperature=settings.get("temperature", 0.1),
            max_tokens=settings.get("max_tokens", 8000),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider_type}")
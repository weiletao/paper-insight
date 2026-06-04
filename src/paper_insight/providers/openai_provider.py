from typing import Optional

import httpx
from openai import OpenAI
from rich.console import Console
from rich.panel import Panel

from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API provider."""

    def __init__(self, base_url: str, api_key: str, model_name: str, temperature: float = 0.1, max_tokens: int = 8000):
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self.console = Console()

    def generate(self, prompt: str, system_prompt: Optional[str] = None, response_format: Optional[dict] = None) -> str:
        """Generate a completion for the given prompt."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
            if response_format:
                kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**kwargs)

            return response.choices[0].message.content.strip()

        except httpx.ConnectError as e:
            error_msg = f"Failed to connect to API: {str(e)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            raise ConnectionError(f"API connection failed: {error_msg}")

        except Exception as e:
            error_msg = f"API request failed: {str(e)}"
            self.console.print(f"[red]Error: {error_msg}[/red]")
            raise RuntimeError(f"API request failed: {error_msg}")

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate completion with JSON response format enforced."""
        return self.generate(prompt, system_prompt, response_format={"type": "json_object"})
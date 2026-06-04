from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a completion for the given prompt."""

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a completion, preferring JSON mode if supported."""
        return self.generate(prompt, system_prompt)

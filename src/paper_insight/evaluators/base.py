from abc import ABC, abstractmethod


class Evaluator(ABC):
    """Base class for paper evaluators."""

    @abstractmethod
    def evaluate(self, content: str):
        """Evaluate the given paper content."""

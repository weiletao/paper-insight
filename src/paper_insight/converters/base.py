from abc import ABC, abstractmethod


class DocumentConverter(ABC):
    """Base class for document converters."""

    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> str:
        """Convert document at input_path and write result to output_path.

        Returns the absolute path to the converted file.
        """

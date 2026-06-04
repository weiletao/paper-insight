import logging
import sys

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str = "paper-insight") -> logging.Logger:
    """Return a logger with a Rich-formatted console handler."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.addHandler(
        RichHandler(
            console=Console(file=sys.stderr),
            rich_tracebacks=True,
            show_level=True,
            show_path=True,
        )
    )

    return logger

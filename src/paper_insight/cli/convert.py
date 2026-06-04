from pathlib import Path

import typer

from paper_insight.config.settings import Settings
from paper_insight.converters.mineru import MinerUConverter
from paper_insight.utils.logger import get_logger

app = typer.Typer(help="Convert documents to markdown.")
logger = get_logger()


@app.callback(invoke_without_command=True)
def convert(
    ctx: typer.Context,
    input_path: str = typer.Argument(..., help="Path to the input PDF file."),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Output directory."),
):
    """Convert a PDF document to markdown."""
    settings = Settings.from_yaml()

    paper_name = Path(input_path).stem
    output_file = Path(output_dir) / paper_name / "paper.md"

    converter = MinerUConverter()

    try:
        result = converter.convert(input_path, str(output_file))
    except FileNotFoundError as exc:
        logger.error(str(exc))
        raise typer.Exit(1) from None
    except RuntimeError as exc:
        logger.error(str(exc))
        raise typer.Exit(1) from None

    typer.echo(f"Conversion completed.")
    typer.echo(f"Saved to: {result}")

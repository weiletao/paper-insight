import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import typer
from rich.progress import Progress, TextColumn, BarColumn

from paper_insight.config.settings import Settings
from paper_insight.converters.mineru import MinerUConverter
from paper_insight.evaluators.paper_reviewer import PaperReviewer
from paper_insight.extractors.paper_section_extractor import PaperSectionExtractor
from paper_insight.providers.factory import create_provider
from paper_insight.ranking.ranker import Ranker
from paper_insight.ranking.roadmap import RoadmapGenerator
from paper_insight.utils.logger import get_logger

app = typer.Typer(add_completion=False, help="Review scientific papers.")
logger = get_logger()


def _review_single_pdf(pdf_path: Path, output_dir: Path, settings: Settings) -> tuple[str, bool]:
    """Review a single PDF. Returns (paper_name, success)."""
    paper_name = pdf_path.stem
    out_dir = output_dir / paper_name
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / "paper.md"

    if md_path.exists():
        logger.info(f"[{paper_name}] Using existing conversion: {md_path}")
    else:
        logger.info(f"[{paper_name}] Converting PDF to markdown...")
        converter = MinerUConverter()
        try:
            converter.convert(str(pdf_path), str(md_path))
        except FileNotFoundError as exc:
            logger.error(f"[{paper_name}] {exc}")
            return paper_name, False
        except RuntimeError as exc:
            logger.error(f"[{paper_name}] {exc}")
            return paper_name, False

    logger.info(f"[{paper_name}] Extracting paper sections...")
    extractor = PaperSectionExtractor()
    sections_path = extractor.save(md_path, out_dir / "sections.json")

    sections = json.loads(Path(sections_path).read_text())

    logger.info(f"[{paper_name}] Starting paper review...")
    provider = create_provider(settings.model.model_dump())
    reviewer = PaperReviewer(provider)

    try:
        reviewer.evaluate(sections, out_dir)
    except Exception as exc:
        logger.error(f"[{paper_name}] Review failed: {exc}")
        return paper_name, False

    return paper_name, True


def _generate_ranking(output_dir: Path, settings: Settings):
    """Generate ranking.md, ranking.csv, and reading-roadmap.md."""
    ranker = Ranker(output_dir)
    scores = ranker.load_scores()
    if not scores:
        logger.warning("No scores found, skipping ranking generation.")
        return

    md_path = ranker.generate_markdown(scores)
    csv_path = ranker.generate_csv(scores)
    typer.echo(f"Ranking: {md_path}")
    typer.echo(f"CSV:     {csv_path}")

    provider = create_provider(settings.model.model_dump())
    roadmap_gen = RoadmapGenerator(provider)
    roadmap_path = roadmap_gen.generate(scores, output_dir)
    typer.echo(f"Roadmap: {roadmap_path}")


@app.command("single")
def review_single(
    input_path: str = typer.Argument(..., help="Path to the input PDF file."),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Output directory."),
):
    """Review a single paper."""
    settings = Settings.from_yaml()
    pdf_path = Path(input_path)
    if not pdf_path.exists():
        logger.error(f"File not found: {input_path}")
        raise typer.Exit(1)

    out_dir = Path(output_dir)
    name, ok = _review_single_pdf(pdf_path, out_dir, settings)
    if ok:
        paper_out = out_dir / name
        typer.echo(f"Review completed for '{name}'.")
        typer.echo(f"  Review: {paper_out / 'review.md'}")
        typer.echo(f"  Score:  {paper_out / 'score.json'}")
    else:
        typer.echo(f"Review failed for '{name}'.")
        raise typer.Exit(1)


@app.command()
def batch(
    input_dir: str = typer.Argument(..., help="Directory containing PDF files."),
    output_dir: str = typer.Option("outputs", "--output", "-o", help="Output directory."),
    force: bool = typer.Option(False, "--force", "-f", help="Re-analyze even if review.md exists."),
    max_workers: int = typer.Option(4, "--workers", "-w", help="Max concurrent workers."),
):
    """Review all papers in a directory. Generates ranking and reading roadmap."""
    in_dir = Path(input_dir)
    if not in_dir.exists():
        logger.error(f"Directory not found: {input_dir}")
        raise typer.Exit(1)

    pdf_files = sorted(in_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in {input_dir}")
        raise typer.Exit(1)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings.from_yaml()

    pending = []
    skipped = 0
    for pdf in pdf_files:
        paper_out = out_dir / pdf.stem / "review.md"
        if force or not paper_out.exists():
            pending.append(pdf)
        else:
            skipped += 1
            logger.info(f"Skipping {pdf.name} (review exists, use --force to re-run)")

    if not pending and skipped:
        typer.echo(f"All {skipped} papers already reviewed. Use --force to re-run.")
        _generate_ranking(out_dir, settings)
        return

    total = len(pending) + skipped
    typer.echo(f"Found {total} PDFs ({len(pending)} to process, {skipped} cached)")

    results: dict[str, bool] = {}
    with Progress(
        TextColumn("[description.description]"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("[cyan]Reviewing papers...", total=len(pending))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_review_single_pdf, pdf, out_dir, settings): pdf
                for pdf in pending
            }
            for future in as_completed(futures):
                pdf = futures[future]
                try:
                    name, ok = future.result()
                    results[name] = ok
                except Exception as exc:
                    logger.error(f"[{pdf.name}] Unexpected error: {exc}")
                    results[pdf.stem] = False
                progress.update(task, advance=1)

    succeeded = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    typer.echo(f"\nCompleted: {succeeded} succeeded, {failed} failed, {skipped} cached")

    _generate_ranking(out_dir, settings)

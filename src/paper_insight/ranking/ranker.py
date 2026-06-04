import csv
from pathlib import Path

from paper_insight.ranking.scorer import PaperScore


def _star_rating(composite: float) -> str:
    """Map composite score to star rating."""
    if composite >= 8.0:
        return "★★★★★ 必读"
    if composite >= 6.5:
        return "★★★★ 值得精读"
    if composite >= 5.0:
        return "★★★ 可选择阅读"
    if composite >= 3.5:
        return "★★ 了解即可"
    return "★ 不建议投入时间"


class Ranker:
    """Load scores from paper output dirs, rank, and generate reports."""

    def __init__(self, output_dir: str | Path):
        self._output_dir = Path(output_dir)

    def load_scores(self) -> list[PaperScore]:
        """Scan outputs/ and load score.json from each paper subdirectory."""
        scores: list[PaperScore] = []
        if not self._output_dir.exists():
            return scores
        for entry in sorted(self._output_dir.iterdir()):
            if entry.is_dir():
                score = PaperScore.from_json(entry)
                if score:
                    scores.append(score)
        # Sort by composite descending.
        scores.sort(key=lambda s: s.composite, reverse=True)
        return scores

    def generate_markdown(self, scores: list[PaperScore], output_path: str | Path | None = None) -> str:
        """Generate a ranking.md with star ratings."""
        lines: list[str] = []
        lines.append("# Paper Ranking\n")
        lines.append(f"Total papers: {len(scores)}\n")

        for i, score in enumerate(scores, 1):
            stars = _star_rating(score.composite)
            lines.append(f"## {i}. {score.paper_name} — {stars}\n")
            lines.append(f"- **综合评分**: {score.composite}/10")
            lines.append(f"- 问题价值: {score.problem_value} | 创新性: {score.innovation} | 技术深度: {score.technical_depth}")
            lines.append(f"- 实验质量: {score.experiment_quality} | 学术影响: {score.academic_impact} | 水论文指数: {score.water_paper_index}")
            lines.append("")

        content = "\n".join(lines)
        out = Path(output_path) if output_path else self._output_dir / "ranking.md"
        out.write_text(content)
        return str(out)

    def generate_csv(self, scores: list[PaperScore], output_path: str | Path | None = None) -> str:
        """Generate a ranking.csv."""
        out = Path(output_path) if output_path else self._output_dir / "ranking.csv"
        with open(out, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "rank", "paper_name", "composite", "star_rating",
                "problem_value", "innovation", "technical_depth",
                "experiment_quality", "academic_impact", "water_paper_index",
            ])
            for i, score in enumerate(scores, 1):
                writer.writerow([
                    i, score.paper_name, score.composite, _star_rating(score.composite),
                    score.problem_value, score.innovation, score.technical_depth,
                    score.experiment_quality, score.academic_impact, score.water_paper_index,
                ])
        return str(out)

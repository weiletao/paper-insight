from pathlib import Path

from paper_insight.ranking.scorer import PaperScore
from paper_insight.utils.logger import get_logger

logger = get_logger()

_ROADMAP_PROMPT = """\
# Role

You are an experienced academic researcher helping plan a reading roadmap.

# Context

Based on the following paper ranking, generate a reading roadmap that suggests the optimal order for reading these papers and explains why.

# Paper Ranking

{ranking}

# Instructions

Please generate a reading roadmap (reading-roadmap.md) with these sections:

## 1. Overview
- Brief summary of the paper collection
- Number of papers, overall quality assessment

## 2. Reading Order
For each paper in recommended reading order:

### Phase 1: Foundation
- Paper name (rank)
- Why read first
- Key takeaways expected

### Phase 2: Core Reading
- Paper name (rank)
- Why read next
- How it builds on prior reading

### Phase 3: Supplementary
- Papers to read selectively based on interest

## 3. Key Insights
- Common themes across papers
- Gaps and opportunities in the field
- Recommended deep-dive papers

## 4. One-Page Summary
A concise table:

| Paper | Priority | Estimated Time | Key Contribution |

Keep it practical and actionable.
"""


class RoadmapGenerator:
    """Generate a reading roadmap from ranked papers via LLM."""

    def __init__(self, provider):
        self._provider = provider

    def generate(self, scores: list[PaperScore], output_dir: str | Path) -> str:
        """Generate reading-roadmap.md from ranked scores.

        Returns the path to the generated file.
        """
        out_dir = Path(output_dir)
        ranking_text = self._build_ranking_text(scores)
        prompt = _ROADMAP_PROMPT.format(ranking=ranking_text)

        logger.info("Generating reading roadmap...")
        response = self._provider.generate(prompt)

        roadmap_path = out_dir / "reading-roadmap.md"
        roadmap_path.write_text(response)
        logger.info(f"Roadmap saved to: {roadmap_path}")
        return str(roadmap_path)

    @staticmethod
    def _build_ranking_text(scores: list[PaperScore]) -> str:
        """Build a compact text representation of the ranking."""
        lines: list[str] = []
        for i, score in enumerate(scores, 1):
            lines.append(
                f"{i}. {score.paper_name} "
                f"(composite={score.composite}, "
                f"innovation={score.innovation}, "
                f"water_paper_index={score.water_paper_index})"
            )
        return "\n".join(lines)

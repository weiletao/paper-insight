import json
import re
from pathlib import Path

from paper_insight.evaluators.base import Evaluator
from paper_insight.utils.logger import get_logger
from paper_insight.utils.prompt_loader import load_prompt

logger = get_logger()

REQUIRED_KEYS = {
    "problem_value",
    "innovation",
    "technical_depth",
    "experiment_quality",
    "academic_impact",
    "water_paper_index",
}

_SCORE_SYSTEM_PROMPT = (
    "You are a scoring assistant. Output ONLY a JSON object with the six scoring keys. "
    "Do not include any prose, explanation, or markdown formatting outside the JSON."
)

_SCORE_EXTRACT_PROMPT = """\
Based on the following paper review, extract the score JSON.
If the review already contains a score block, reproduce it exactly.
If not, infer scores from the review content.

Review:
{review_text}

Output only the JSON object:
```json
{{
  "problem_value": <1-10>,
  "innovation": <1-10>,
  "technical_depth": <1-10>,
  "experiment_quality": <1-10>,
  "academic_impact": <1-10>,
  "water_paper_index": <1-10>
}}
```"""


class PaperReviewer(Evaluator):
    """Review a paper by sections using an LLM provider."""

    def __init__(self, provider):
        self._provider = provider

    def evaluate(self, sections: dict, output_dir: str | Path) -> tuple[str, str]:
        """Run the review pipeline.

        Returns (review_md_path, score_json_path).
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        prompt = self._build_prompt(sections)
        logger.info("Calling LLM for paper review...")
        response = self._provider.generate(prompt)

        score_path = out_dir / "score.json"
        score = self._extract_score(response)
        if score is None:
            logger.info("Score JSON not found in review, retrying with JSON mode...")
            score = self._extract_score_fallback(response)

        if score:
            score_path.write_text(json.dumps(score, ensure_ascii=False, indent=2))
            logger.info(f"Score saved to: {score_path}")

            # Compute composite and star rating, append to review
            comp = _compute_composite(score)
            stars = _star_rating(comp)
            review_text = response + f"\n\n---\n\n**综合评分: {comp}/10**  \n**星级: {stars}**\n"
        else:
            review_text = response
            logger.warning("Could not parse score JSON from LLM response.")

        review_path = out_dir / "review.md"
        review_path.write_text(review_text)
        logger.info(f"Review saved to: {review_path}")

        return str(review_path), str(score_path)

    def _build_prompt(self, sections: dict) -> str:
        """Build the review prompt from extracted sections."""
        context = {
            "title": sections.get("title", "N/A"),
            "abstract": sections.get("abstract", "N/A"),
            "introduction": sections.get("introduction", "N/A"),
            "method": sections.get("method", "N/A"),
            "experiment": sections.get("experiment", "N/A"),
            "conclusion": sections.get("conclusion", "N/A"),
        }
        return load_prompt("deep_review.md", **context)

    @staticmethod
    def _extract_score(text: str) -> dict | None:
        """Extract and validate the JSON scoring block from the LLM response."""
        # Strategy 1: Match ```json { ... } ``` blocks.
        json_block_pattern = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.DOTALL)
        for block in json_block_pattern.findall(text):
            data = _try_parse(block)
            if data and _is_valid_score(data):
                return _normalize_score(data)

        # Strategy 2: Match bare ``` { ... } ``` blocks.
        bare_block_pattern = re.compile(r"```\s*(\{[\s\S]*?\})\s*```", re.DOTALL)
        for block in bare_block_pattern.findall(text):
            data = _try_parse(block)
            if data and _is_valid_score(data):
                return _normalize_score(data)

        # Strategy 3: Find standalone JSON objects (heuristic: brace pairs at line start).
        for m in re.finditer(r"(?m)^\s*(\{[\s\S]*?\})\s*$", text):
            data = _try_parse(m.group(1))
            if data and _is_valid_score(data):
                return _normalize_score(data)

        return None

    def _extract_score_fallback(self, review_text: str) -> dict | None:
        """Fallback: ask LLM in JSON mode to extract score from the review text."""
        truncated = review_text[:15000]  # keep prompt within reasonable bounds
        prompt = _SCORE_EXTRACT_PROMPT.format(review_text=truncated)
        raw = self._provider.generate_json(prompt, system_prompt=_SCORE_SYSTEM_PROMPT)
        data = _try_parse(raw)
        if data and _is_valid_score(data):
            return _normalize_score(data)
        return None


def _try_parse(raw: str) -> dict | None:
    """Try to parse a raw JSON string, return None on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _is_valid_score(data: dict) -> bool:
    """Check if a dict has all required keys with numeric values."""
    if not REQUIRED_KEYS.issubset(data.keys()):
        return False
    for key in REQUIRED_KEYS:
        if not isinstance(data[key], (int, float)):
            return False
    return True


def _normalize_score(data: dict) -> dict:
    """Clamp score values to valid ranges."""
    return {
        "problem_value": _clamp(data["problem_value"], 1, 10),
        "innovation": _clamp(data["innovation"], 1, 10),
        "technical_depth": _clamp(data["technical_depth"], 1, 10),
        "experiment_quality": _clamp(data["experiment_quality"], 1, 10),
        "academic_impact": _clamp(data["academic_impact"], 1, 10),
        "water_paper_index": _clamp(data["water_paper_index"], 1, 10),
    }


def _clamp(value: int | float, lo: int, hi: int) -> int:
    """Clamp a numeric value to [lo, hi] and return int."""
    return int(max(lo, min(hi, value)))


def _compute_composite(score: dict) -> float:
    """Compute composite score from a score dict."""
    avg = (score["problem_value"] + score["innovation"] + score["technical_depth"]
           + score["experiment_quality"] + score["academic_impact"]) / 5
    return round(avg - score["water_paper_index"] / 10, 1)


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

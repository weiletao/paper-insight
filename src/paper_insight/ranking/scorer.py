import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PaperScore:
    paper_name: str
    problem_value: float
    innovation: float
    technical_depth: float
    experiment_quality: float
    academic_impact: float
    water_paper_index: float
    composite: float

    @classmethod
    def from_json(cls, dir_path: Path) -> "PaperScore | None":
        score_file = dir_path / "score.json"
        if not score_file.exists():
            return None
        data = json.loads(score_file.read_text())
        pv = _clamp(_num(data, "problem_value"))
        inn = _clamp(_num(data, "innovation"))
        td = _clamp(_num(data, "technical_depth"))
        eq = _clamp(_num(data, "experiment_quality"))
        ai = _clamp(_num(data, "academic_impact"))
        wp = _clamp(_num(data, "water_paper_index"))
        # Composite: average of positive dimensions minus water penalty.
        comp = round(((pv + inn + td + eq + ai) / 5) - (wp / 10), 2)
        return cls(
            paper_name=dir_path.name,
            problem_value=pv,
            innovation=inn,
            technical_depth=td,
            experiment_quality=eq,
            academic_impact=ai,
            water_paper_index=wp,
            composite=comp,
        )


def _num(data: dict, key: str) -> float:
    val = data.get(key, 0)
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    """Clamp a score to [1, 10]."""
    return max(1.0, min(10.0, value))

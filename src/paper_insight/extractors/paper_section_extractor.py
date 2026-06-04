import json
import re
from pathlib import Path


# Mapping from normalized heading text to section keys.
_SECTION_MAP = {
    "abstract": "abstract",
    "introduction": "introduction",
    "method": "method",
    "approach": "method",
    "methodology": "method",
    "proposed method": "method",
    "method and approach": "method",
    "experiment": "experiment",
    "experiments": "experiment",
    "evaluation": "experiment",
    "evaluations": "experiment",
    "experimental results": "experiment",
    "results": "experiment",
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "discussion": "conclusion",
    "future work": "conclusion",
    "references": "references",
}


def _normalize(heading: str) -> str:
    """Normalize a markdown heading for section matching."""
    text = heading.strip().lower()
    # Remove leading numbers like "1.", "2.1", "III"
    text = re.sub(r"^\s*[\d\.\-\s]+", "", text)
    return text.strip()


def _match_section_key(normalized: str) -> str | None:
    """Match a normalized heading to a canonical section key."""
    # Exact match first.
    if normalized in _SECTION_MAP:
        return _SECTION_MAP[normalized]
    # Check if any known heading is a substring of the normalized text.
    for known, mapped_key in _SECTION_MAP.items():
        if known in normalized:
            return mapped_key
    # Check if the first token matches.
    first_token = normalized.split()[0] if normalized.split() else ""
    if first_token in _SECTION_MAP:
        return _SECTION_MAP[first_token]
    return None


class PaperSectionExtractor:
    """Extract structured sections from a markdown-converted paper."""

    def extract(self, markdown_path: str | Path) -> dict:
        """Parse the markdown file and return a dict of section texts."""
        path = Path(markdown_path)
        lines = path.read_text().split("\n")

        # Find all heading line indices and their raw text.
        heading_re = re.compile(r"^(#+)\s+(.*)$")
        headings: list[tuple[int, str, int]] = []  # (line_idx, text, level)
        for i, line in enumerate(lines):
            m = heading_re.match(line)
            if m:
                headings.append((i, m.group(2), len(m.group(1))))

        if not headings:
            return {"content": "\n".join(lines).strip()}

        sections: dict[str, list[str]] = {}

        for idx, (line_idx, raw_heading, level) in enumerate(headings):
            # Content is between this heading line and the next heading of
            # equal or higher level (i.e., same or fewer # marks).
            content_start = line_idx + 1
            if idx + 1 < len(headings):
                content_end = headings[idx + 1][0]
            else:
                content_end = len(lines)

            section_lines = lines[content_start:content_end]
            # Strip trailing blank lines.
            while section_lines and not section_lines[-1].strip():
                section_lines.pop()
            section_text = "\n".join(section_lines)

            if not section_text.strip():
                continue

            normalized = _normalize(raw_heading)
            key = _match_section_key(normalized)
            if not key:
                key = f"section_{normalized[:30]}" if normalized else f"section_{idx}"

            sections.setdefault(key, []).append(section_text)

        # Merge multiple blocks per key.
        return {k: "\n\n".join(blocks) for k, blocks in sections.items()}

    def save(self, markdown_path: str | Path, output_path: str | Path) -> str:
        """Extract sections and save as JSON. Returns the output path."""
        sections = self.extract(markdown_path)
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(sections, ensure_ascii=False, indent=2))
        return str(out)

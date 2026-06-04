from pathlib import Path

_PROMPTS_DIR = Path(__file__).parents[3] / "prompts"


def load_prompt(template_name: str, **kwargs) -> str:
    """Load a prompt template from the prompts/ directory and format with kwargs."""
    template_path = _PROMPTS_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    template = template_path.read_text()
    if kwargs:
        return template.format(**kwargs)
    return template

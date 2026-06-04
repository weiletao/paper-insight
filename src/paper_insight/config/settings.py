from pathlib import Path

import yaml
from pydantic import BaseModel


class ModelConfig(BaseModel):
    provider: str = "openai-compatible"
    base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    temperature: float = 0.1
    max_tokens: int = 8000


class ConverterConfig(BaseModel):
    provider: str = "mineru"


class AppConfig(BaseModel):
    name: str = "paper-insight"


class Settings(BaseModel):
    app: AppConfig = AppConfig()
    model: ModelConfig = ModelConfig()
    converter: ConverterConfig = ConverterConfig()

    @classmethod
    def from_yaml(cls, path: Path | str = "config/config.yaml") -> "Settings":
        path = Path(path)
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text()) or {}
        return cls(
            app=AppConfig(**data.get("app", {})),
            model=ModelConfig(**data.get("model", {})),
            converter=ConverterConfig(**data.get("converter", {})),
        )

"""Load and validate project configuration from config.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.toml"

DEFAULTS = {
    "model": {
        "provider": "anthropic",
        "name": "claude-opus-4-6",
        "max_tokens": 4096,
        "temperature": 1.0,
    },
    "briefing": {
        "provider": "anthropic",
        "name": "claude-opus-4-6",
        "max_tokens": 4096,
        "temperature": 1.0,
    },
    "budget": {
        "max_tokens_per_session": 500_000,
        "warn_at_percent": 80,
    },
}


@dataclass
class ModelConfig:
    provider: str
    name: str
    max_tokens: int
    temperature: float


@dataclass
class BudgetConfig:
    max_tokens_per_session: int
    warn_at_percent: int


@dataclass
class Config:
    model: ModelConfig
    briefing: ModelConfig
    budget: BudgetConfig


def load_config(path: Path = CONFIG_PATH) -> Config:
    """Read config.toml and return a typed Config, falling back to defaults."""
    if path.exists():
        raw = tomllib.loads(path.read_text())
    else:
        raw = {}

    # Model section
    m = raw.get("model", {})
    briefing_raw = m.pop("briefing", {})  # nested under [model.briefing]

    model = ModelConfig(
        provider=m.get("provider", DEFAULTS["model"]["provider"]),
        name=m.get("name", DEFAULTS["model"]["name"]),
        max_tokens=m.get("max_tokens", DEFAULTS["model"]["max_tokens"]),
        temperature=m.get("temperature", DEFAULTS["model"]["temperature"]),
    )

    briefing = ModelConfig(
        provider=briefing_raw.get("provider", DEFAULTS["briefing"]["provider"]),
        name=briefing_raw.get("name", DEFAULTS["briefing"]["name"]),
        max_tokens=briefing_raw.get("max_tokens", DEFAULTS["briefing"]["max_tokens"]),
        temperature=briefing_raw.get("temperature", DEFAULTS["briefing"]["temperature"]),
    )

    # Budget section
    b = raw.get("budget", {})
    budget = BudgetConfig(
        max_tokens_per_session=b.get("max_tokens_per_session", DEFAULTS["budget"]["max_tokens_per_session"]),
        warn_at_percent=b.get("warn_at_percent", DEFAULTS["budget"]["warn_at_percent"]),
    )

    return Config(model=model, briefing=briefing, budget=budget)

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class JobPreferences:
    target_roles: list[str] = field(default_factory=list)
    preferred_locations: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)
    minimum_score: float = 50.0


def load_job_preferences(path: str | Path) -> JobPreferences:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Job preferences file not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    return JobPreferences(
        target_roles=data.get("target_roles", []) or [],
        preferred_locations=data.get("preferred_locations", []) or [],
        required_terms=data.get("required_terms", []) or [],
        minimum_score=float(data.get("minimum_score", 50.0)),
    )
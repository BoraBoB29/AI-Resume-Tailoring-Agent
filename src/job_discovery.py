from pathlib import Path

import yaml

from src.job_ingestion.pipeline import discover_jobs


def load_search_config(path="data/job_search_config.yaml"):
    config_path = Path(path)

    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def discover_matching_jobs(
    adapter,
    config_path="data/job_search_config.yaml",
    min_score=None,
):
    config = load_search_config(config_path)

    effective_min_score = (
        config.get("minimum_match_score", 0)
        if min_score is None
        else min_score
    )

    return discover_jobs(
        adapter=adapter,
        target_roles=config.get("target_roles", []),
        preferred_locations=config.get("preferred_locations", []),
        required_terms=config.get("required_terms", []),
        min_score=effective_min_score,
    )
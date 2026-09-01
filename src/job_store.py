from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.job_ingestion.models import Job
from src.job_matcher import JobMatchResult


DEFAULT_STORE_PATH = Path("data/jobs/job_store.json")


def _job_to_dict(job: Job) -> dict:
    """
    Convert a Job object into JSON-safe data.
    """
    return asdict(job)


def _match_to_dict(match: JobMatchResult) -> dict:
    """
    Convert a JobMatchResult into JSON-safe data.
    """
    return {
        "job": _job_to_dict(match.job),
        "score": match.score,
        "matched_terms": match.matched_terms,
        "missing_terms": match.missing_terms,
    }


def save_matches(
    matches: list[JobMatchResult],
    path: str | Path = DEFAULT_STORE_PATH,
) -> Path:
    """
    Save discovered job matches to disk.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "jobs": [
            _match_to_dict(match)
            for match in matches
        ]
    }

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path


def load_matches(
    path: str | Path = DEFAULT_STORE_PATH,
) -> list[dict]:
    """
    Load previously saved job matches.

    Returns dictionaries rather than JobMatchResult objects
    because this is intended as a lightweight persistence layer.
    """

    path = Path(path)

    if not path.exists():
        return []

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return data.get("jobs", [])


def add_match(
    match: JobMatchResult,
    path: str | Path = DEFAULT_STORE_PATH,
) -> Path:
    """
    Add one job match to the persistent store.
    """

    existing = load_matches(path)

    existing_job_ids = {
        item.get("job", {}).get("job_id")
        for item in existing
    }

    job_id = match.job.job_id

    if job_id not in existing_job_ids:
        existing.append(
            _match_to_dict(match)
        )

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            {"jobs": existing},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return path
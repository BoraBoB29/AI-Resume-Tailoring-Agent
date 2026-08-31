from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.job_ingestion.models import Job


@dataclass
class JobMatchResult:
    job: Job
    score: float
    matched_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#./ -]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score_job(
    job: Job,
    target_roles: list[str],
    preferred_locations: list[str] | None = None,
    required_terms: list[str] | None = None,
) -> JobMatchResult:
    """
    Deterministically score a job against basic candidate preferences.

    This is intentionally cheap and explainable. It does not call an LLM.
    """
    target_roles = target_roles or []
    preferred_locations = preferred_locations or []
    required_terms = required_terms or []

    title = _normalize(job.title)
    location = _normalize(job.location or "")
    description = _normalize(job.description)

    matched_terms: list[str] = []
    missing_terms: list[str] = []

    score = 0.0

    # Role/title match.
    role_matches = 0
    for role in target_roles:
        if _normalize(role) in title:
            role_matches += 1
            matched_terms.append(role)

    if target_roles:
        score += min(role_matches / len(target_roles), 1.0) * 50

    # Location match.
    if preferred_locations:
        location_matches = 0
        for preferred in preferred_locations:
            if _normalize(preferred) in location:
                location_matches += 1
                matched_terms.append(preferred)

        score += min(
            location_matches / len(preferred_locations),
            1.0,
        ) * 20

    # Required-term match.
    if required_terms:
        matched_required = 0

        for term in required_terms:
            normalized_term = _normalize(term)

            if normalized_term and normalized_term in description:
                matched_required += 1
                matched_terms.append(term)
            else:
                missing_terms.append(term)

        score += (
            matched_required / len(required_terms)
        ) * 30

    return JobMatchResult(
        job=job,
        score=round(min(score, 100.0), 2),
        matched_terms=_unique(matched_terms),
        missing_terms=_unique(missing_terms),
    )


def filter_jobs(
    jobs: list[Job],
    target_roles: list[str],
    preferred_locations: list[str] | None = None,
    required_terms: list[str] | None = None,
    minimum_score: float = 50.0,
) -> list[JobMatchResult]:

    results = []

    for job in jobs:
        result = score_job(
            job,
            target_roles=target_roles,
            preferred_locations=preferred_locations,
            required_terms=required_terms,
        )

        if result.score >= minimum_score:
            results.append(result)

    return sorted(
        results,
        key=lambda result: result.score,
        reverse=True,
    )


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []

    for value in values:
        key = value.lower()

        if key not in seen:
            seen.add(key)
            result.append(value)

    return result
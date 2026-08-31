from src.job_ingestion.match_result import JobMatch
from src.job_matcher import score_job


def discover_jobs(
    adapter,
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
    min_score=0,
    **fetch_kwargs,
):
    jobs = adapter.fetch_jobs(**fetch_kwargs)

    results = []

    for job in jobs:
        match_result = score_job(
            job,
            target_roles=target_roles or [],
            preferred_locations=preferred_locations or [],
            required_terms=required_terms or [],
        )

        score = getattr(match_result, "score", 0)

        if score < min_score:
            continue

        results.append(
            JobMatch(
                job=job,
                score=score,
                matched_terms=getattr(
                    match_result,
                    "matched_terms",
                    [],
                ),
                missing_terms=getattr(
                    match_result,
                    "missing_terms",
                    [],
                ),
            )
        )

    results.sort(
        key=lambda result: result.score,
        reverse=True,
    )

    return results
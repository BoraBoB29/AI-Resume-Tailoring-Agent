from src.job_matcher import score_job


def discover_matching_jobs(
    adapter,
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
    minimum_score=50.0,
    **fetch_kwargs,
):
    jobs = adapter.fetch_jobs(**fetch_kwargs)

    results = []

    for job in jobs:
        result = score_job(
            job,
            target_roles=target_roles or [],
            preferred_locations=preferred_locations or [],
            required_terms=required_terms or [],
        )

        if result.score >= minimum_score:
            results.append(result)

    return sorted(
        results,
        key=lambda result: result.score,
        reverse=True,
    )


def discover_jobs(
    adapter,
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
    minimum_score=50.0,
    min_score=None,
    **fetch_kwargs,
):
    """
    Discover and rank jobs.

    Returns JobMatchResult objects so callers have access to:
    - result.job
    - result.score
    - result.matched_terms
    - result.missing_terms

    min_score is supported as a backward-compatible alias.
    """

    if min_score is not None:
        minimum_score = min_score

    return discover_matching_jobs(
        adapter=adapter,
        target_roles=target_roles,
        preferred_locations=preferred_locations,
        required_terms=required_terms,
        minimum_score=minimum_score,
        **fetch_kwargs,
    )

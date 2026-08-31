from src.job_matcher import score_job


def discover_jobs(
    adapter,
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
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

        results.append((job, match_result))

    results.sort(
        key=lambda item: getattr(item[1], "score", 0),
        reverse=True,
    )

    return [job for job, _ in results]

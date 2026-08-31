from __future__ import annotations

from src.job_ingestion.pipeline import discover_matching_jobs
from src.job_ingestion.resume_bridge import generate_resume_for_job


def process_best_job(
    adapter,
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
    minimum_score=50.0,
    master_resume_path=None,
    max_iterations=None,
    **fetch_kwargs,
):
    """
    Discover matching jobs, select the highest-scoring job,
    and generate a tailored resume for it.
    """

    results = discover_matching_jobs(
        adapter=adapter,
        target_roles=target_roles,
        preferred_locations=preferred_locations,
        required_terms=required_terms,
        minimum_score=minimum_score,
        **fetch_kwargs,
    )

    if not results:
        return None

    best_match = results[0]

    pdf_path = generate_resume_for_job(
        job=best_match.job,
        master_resume_path=master_resume_path,
        max_iterations=max_iterations,
    )

    return {
        "job": best_match.job,
        "score": best_match.score,
        "matched_terms": best_match.matched_terms,
        "missing_terms": best_match.missing_terms,
        "pdf_path": pdf_path,
    }
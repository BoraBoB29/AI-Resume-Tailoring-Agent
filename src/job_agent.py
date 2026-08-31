from __future__ import annotations

from dataclasses import dataclass

from src.job_ingestion.models import Job
from src.job_matcher import JobMatchResult, filter_jobs
from src.job_resume_pipeline import generate_resume_for_job


@dataclass
class JobAgent:
    adapter: object

    def discover(
        self,
        target_roles: list[str],
        preferred_locations: list[str] | None = None,
        required_terms: list[str] | None = None,
        minimum_score: float = 50.0,
        **fetch_kwargs,
    ) -> list[JobMatchResult]:
        """
        Discover jobs from the configured adapter and rank/filter them.

        Additional keyword arguments are passed directly to the adapter.
        This allows source-specific parameters such as a Greenhouse
        board token to be supplied at discovery time.
        """

        jobs = self.adapter.fetch_jobs(**fetch_kwargs)

        return filter_jobs(
            jobs,
            target_roles=target_roles,
            preferred_locations=preferred_locations or [],
            required_terms=required_terms or [],
            minimum_score=minimum_score,
        )

    def generate_resume(
        self,
        match: JobMatchResult,
        max_iterations: int | None = None,
    ):
        """
        Generate a tailored resume for a selected job match.
        """

        if not isinstance(match, JobMatchResult):
            raise TypeError("match must be a JobMatchResult.")

        job = match.job

        if not isinstance(job, Job):
            raise TypeError("match.job must be a Job instance.")

        if not job.title.strip():
            raise ValueError("Selected job has no title.")

        if not job.company.strip():
            raise ValueError("Selected job has no company.")

        if not job.description.strip():
            raise ValueError("Selected job has no description.")

        return generate_resume_for_job(
            job,
            max_iterations=max_iterations,
        )

from __future__ import annotations

from pathlib import Path

from src.resume_generator import generate_resume
from src.job_ingestion.models import Job


def generate_resume_for_job(
    job: Job,
    master_resume_path: str | None = None,
    max_iterations: int | None = None,
    strict_one_page: bool = True,
):
    """
    Feed a discovered Job into the existing resume generation pipeline.
    """

    if not job.description.strip():
        raise ValueError(
            f"Job '{job.title}' has no description."
        )

    return generate_resume(
        job_description=job.description,
        company=job.company,
        role=job.title,
        master_resume_path=master_resume_path,
        strict_one_page=strict_one_page,
        max_iterations=max_iterations,
    )
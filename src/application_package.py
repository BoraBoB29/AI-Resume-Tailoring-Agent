from __future__ import annotations

import json
import re
from pathlib import Path

from src.job_ingestion.models import Job
from src.job_matcher import JobMatchResult


def create_cover_letter(
    match: JobMatchResult,
    output_dir: str | Path,
) -> Path:
    """
    Create a cover-letter text file for a matched job.

    Parameters
    ----------
    match:
        JobMatchResult containing the selected job.

    output_dir:
        Directory where the cover letter should be created.

    Returns
    -------
    Path
        Path to the generated cover-letter file.
    """

    if not isinstance(match, JobMatchResult):
        raise TypeError("match must be a JobMatchResult.")

    job = match.job

    if not isinstance(job, Job):
        raise TypeError("match.job must be a Job instance.")

    if not job.title.strip():
        raise ValueError("Job has no title.")

    if not job.company.strip():
        raise ValueError("Job has no company.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{_safe_filename(job.company)}_"
        f"{_safe_filename(job.title)}_cover_letter.txt"
    )

    cover_letter_path = output_path / filename

    matched_terms = match.matched_terms or []

    alignment_sentence = ""

    if matched_terms:
        terms = ", ".join(matched_terms[:5])

        alignment_sentence = (
            f"\n\nMy background aligns with areas such as {terms}, "
            "and I am interested in applying that experience to this role."
        )

    cover_letter = (
        "Dear Hiring Team,\n\n"
        f"I am writing to express my interest in the {job.title} "
        f"position at {job.company}. "
        "I am excited about the opportunity to contribute to the team "
        "and apply my skills to the responsibilities of this position."
        f"{alignment_sentence}\n\n"
        "I would welcome the opportunity to discuss how my background "
        "could contribute to your team. Thank you for your consideration."
        "\n\n"
        "Best regards,\n"
        "Candidate\n"
    )

    cover_letter_path.write_text(
        cover_letter,
        encoding="utf-8",
    )

    return cover_letter_path


def create_application_metadata(
    match: JobMatchResult,
    output_dir: str | Path,
) -> Path:
    """
    Create application metadata JSON for a matched job.

    Returns the path to the generated JSON file.
    """

    if not isinstance(match, JobMatchResult):
        raise TypeError("match must be a JobMatchResult.")

    job = match.job

    if not isinstance(job, Job):
        raise TypeError("match.job must be a Job instance.")

    if not job.title.strip():
        raise ValueError("Job has no title.")

    if not job.company.strip():
        raise ValueError("Job has no company.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    metadata = {
        "status": "READY_TO_APPLY",
        "job": {
            "title": job.title,
            "company": job.company,
            "location": job.location or "",
            "url": job.url or "",
            "job_id": job.job_id or "",
        },
        "match": {
            "score": float(match.score),
            "matched_terms": list(match.matched_terms),
            "missing_terms": list(match.missing_terms),
        },
    }
    metadata_path = output_path / "application_metadata.json"

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return metadata_path


def create_application_package(
    match: JobMatchResult,
    output_dir: str | Path,
) -> dict[str, Path]:
    """
    Create the complete application package.

    The package currently contains:
        - cover letter
        - application metadata
    """

    if not isinstance(match, JobMatchResult):
        raise TypeError("match must be a JobMatchResult.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    cover_letter_path = create_cover_letter(
        match,
        output_path,
    )

    metadata_path = create_application_metadata(
        match,
        output_path,
    )

    return {
        "cover_letter": cover_letter_path,
        "metadata": metadata_path,
    }


def _safe_filename(value: str) -> str:
    """
    Convert a value into a safe filename component.
    """

    value = value.strip()

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value,
    )

    value = re.sub(
        r"\s+",
        "_",
        value,
    )

    value = value.strip("._")

    return value[:100] or "unknown"
from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.job_matcher import JobMatchResult
from src.job_resume_pipeline import generate_resume_for_job


DEFAULT_OUTPUT_DIR = Path("output/applications")


def _slugify(value: str) -> str:
    """
    Convert a company/job title into a safe directory name.
    """

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


def _create_output_directory(
    match: JobMatchResult,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Path:

    job = match.job

    company_slug = _slugify(
        job.company
    )

    role_slug = _slugify(
        job.title
    )

    directory = (
        Path(output_dir)
        / company_slug
        / role_slug
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def create_application_metadata(
    match: JobMatchResult,
    output_directory: Path,
) -> Path:
    """
    Save application metadata for the selected job.
    """

    job = match.job

    metadata = {
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "status": "READY_TO_APPLY",

        "job": {
            "id": job.job_id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "source": job.source,
        },

        "match": {
            "score": match.score,
            "matched_terms": match.matched_terms,
            "missing_terms": match.missing_terms,
        },

        "files": {
            "resume": None,
            "cover_letter": None,
        },
    }

    metadata_path = (
        output_directory
        / "application.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return metadata_path


def create_cover_letter(
    match: JobMatchResult,
    output_directory: Path,
) -> Path:
    """
    Create a simple evidence-based cover letter.

    This version deliberately does not invent experience,
    achievements, or qualifications.
    """

    job = match.job

    matched = (
        ", ".join(match.matched_terms)
        if match.matched_terms
        else "the role requirements"
    )

    content = f"""Dear Hiring Team,

I am writing to express my interest in the {job.title} position at {job.company}.

My background and experience align with several aspects of this opportunity, particularly {matched}. I would welcome the opportunity to bring my experience to your team and contribute to the role's objectives.

I am particularly interested in this position because it offers an opportunity to apply my experience while continuing to grow in a role aligned with my professional background.

Thank you for considering my application. I would welcome the opportunity to discuss my background and suitability for the position.

Best regards,
Varun Bora
"""

    path = (
        output_directory
        / "cover_letter.txt"
    )

    path.write_text(
        content,
        encoding="utf-8",
    )

    return path


def prepare_application(
    match: JobMatchResult,
    max_iterations: int | None = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> dict:
    """
    Generate the complete application package.

    Returns paths to the generated files.
    """

    if not isinstance(
        match,
        JobMatchResult,
    ):
        raise TypeError(
            "match must be a JobMatchResult."
        )

    output_directory = (
        _create_output_directory(
            match,
            output_dir,
        )
    )

    print(
        "\nPreparing application package..."
    )

    print(
        "\n[1/3] Generating tailored resume..."
    )

    resume_path = generate_resume_for_job(
        match.job,
        max_iterations=max_iterations,
    )

    print(
        "\n[2/3] Generating cover letter..."
    )

    cover_letter_path = create_cover_letter(
        match,
        output_directory,
    )

    print(
        "\n[3/3] Saving application metadata..."
    )

    metadata_path = create_application_metadata(
        match,
        output_directory,
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    metadata["files"]["resume"] = str(
        resume_path
    )

    metadata["files"]["cover_letter"] = str(
        cover_letter_path
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return {
        "directory": output_directory,
        "resume": Path(resume_path),
        "cover_letter": cover_letter_path,
        "metadata": metadata_path,
    }
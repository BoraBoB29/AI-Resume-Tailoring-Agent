from src.job_ingestion.models import Job
from src.job_matcher import JobMatchResult
from src.application_package import (
    create_cover_letter,
    create_application_metadata,
)


def create_test_match():

    job = Job(
        title="Product Manager",
        company="Example Corp",
        location="Pune, India",
        description="Product management and analytics.",
        url="https://example.com/jobs/123",
        source="greenhouse",
        job_id="123",
    )

    return JobMatchResult(
        job=job,
        score=80.0,
        matched_terms=[
            "Product Manager",
            "analytics",
        ],
        missing_terms=[],
    )


def test_create_cover_letter(tmp_path):

    match = create_test_match()

    path = create_cover_letter(
        match,
        tmp_path,
    )

    assert path.exists()

    content = path.read_text(
        encoding="utf-8"
    )

    assert "Product Manager" in content
    assert "Example Corp" in content


def test_create_application_metadata(
    tmp_path,
):

    match = create_test_match()

    path = create_application_metadata(
        match,
        tmp_path,
    )

    assert path.exists()

    content = path.read_text(
        encoding="utf-8"
    )

    assert "READY_TO_APPLY" in content
    assert "Product Manager" in content
    assert "Example Corp" in content
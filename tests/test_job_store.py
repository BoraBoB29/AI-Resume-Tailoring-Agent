from src.job_ingestion.models import Job
from src.job_matcher import JobMatchResult
from src.job_store import save_matches, load_matches


def test_save_and_load_matches(tmp_path):
    job = Job(
        title="Product Manager",
        company="Example Corp",
        location="Pune, India",
        description="Product management and analytics.",
        url="https://example.com/job/1",
        source="greenhouse",
        job_id="1",
    )

    match = JobMatchResult(
        job=job,
        score=80.0,
        matched_terms=["Product Manager"],
        missing_terms=[],
    )

    path = tmp_path / "jobs.json"

    save_matches(
        [match],
        path=path,
    )

    results = load_matches(path)

    assert len(results) == 1
    assert results[0]["job"]["title"] == "Product Manager"
    assert results[0]["score"] == 80.0
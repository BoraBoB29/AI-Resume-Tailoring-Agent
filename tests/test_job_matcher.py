from src.job_ingestion.models import Job
from src.job_matcher import filter_jobs, score_job


def make_job(
    title,
    location="Pune, India",
    description="Product management with SQL and Python.",
):
    return Job(
        title=title,
        company="TestCompany",
        location=location,
        description=description,
    )


def test_score_job_matches_title_location_and_terms():
    job = make_job(
        "Product Manager",
        "Pune, India",
        "Product management, SQL, Python, analytics.",
    )

    result = score_job(
        job,
        target_roles=["Product Manager"],
        preferred_locations=["Pune"],
        required_terms=["SQL", "Python"],
    )

    assert result.score == 100.0
    assert "Product Manager" in result.matched_terms
    assert "Pune" in result.matched_terms
    assert "SQL" in result.matched_terms
    assert "Python" in result.matched_terms


def test_score_job_records_missing_terms():
    job = make_job(
        "Product Manager",
        "Pune, India",
        "Product management with SQL.",
    )

    result = score_job(
        job,
        target_roles=["Product Manager"],
        preferred_locations=["Pune"],
        required_terms=["SQL", "Python"],
    )

    assert "SQL" in result.matched_terms
    assert "Python" in result.missing_terms
    assert result.score < 100.0


def test_filter_jobs_removes_low_score_jobs():
    good = make_job(
        "Product Manager",
        "Pune, India",
        "Product management SQL Python analytics.",
    )

    bad = make_job(
        "Software Engineer",
        "New York",
        "Backend systems and Java.",
    )

    results = filter_jobs(
        [good, bad],
        target_roles=["Product Manager"],
        preferred_locations=["Pune"],
        required_terms=["SQL"],
        minimum_score=50.0,
    )

    assert len(results) == 1
    assert results[0].job.title == "Product Manager"


def test_filter_jobs_sorts_by_score():
    high = make_job(
        "Product Manager",
        "Pune, India",
        "Product management SQL Python analytics.",
    )

    medium = make_job(
        "Product Analyst",
        "Pune, India",
        "Analytics SQL.",
    )

    results = filter_jobs(
        [medium, high],
        target_roles=["Product Manager", "Product Analyst"],
        preferred_locations=["Pune"],
        required_terms=["SQL"],
        minimum_score=0.0,
    )

    assert results[0].score >= results[1].score
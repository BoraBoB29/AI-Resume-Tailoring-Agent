import pytest

from src.job_ingestion.normalizer import normalize_job


def test_normalize_job():
    job = normalize_job({
        "title": "Product Manager",
        "company": "TestCompany",
        "location": "Pune, India",
        "description": "Manage product development.",
        "url": "https://example.com/job/123",
        "source": "test",
        "skills": ["SQL", "Python"],
    })

    assert job.title == "Product Manager"
    assert job.company == "TestCompany"
    assert job.location == "Pune, India"
    assert job.skills == ["SQL", "Python"]


def test_normalize_job_requires_title():
    with pytest.raises(ValueError):
        normalize_job({
            "company": "TestCompany",
        })


def test_normalize_job_requires_company():
    with pytest.raises(ValueError):
        normalize_job({
            "title": "Product Manager",
        })


def test_normalize_optional_fields():
    job = normalize_job({
        "title": "Analyst",
        "company": "TestCompany",
    })

    assert job.location is None
    assert job.url is None
    assert job.skills == []
    assert job.requirements == []
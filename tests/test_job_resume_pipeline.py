from src.job_ingestion.models import Job
from src.job_resume_pipeline import generate_resume_for_job


def test_generate_resume_for_job_passes_job_data(monkeypatch):
    captured = {}

    def fake_generate_resume(**kwargs):
        captured.update(kwargs)
        return "output/test.pdf"

    monkeypatch.setattr(
        "src.job_resume_pipeline.generate_resume",
        fake_generate_resume,
    )

    job = Job(
        title="Product Manager",
        company="Example Corp",
        location="Pune, India",
        description="Manage product roadmap and work with engineering teams.",
        url="https://example.com/job/123",
        source="greenhouse",
        job_id="123",
    )

    result = generate_resume_for_job(job)

    assert result == "output/test.pdf"
    assert captured["job_description"] == job.description
    assert captured["company"] == "Example Corp"
    assert captured["role"] == "Product Manager"


def test_generate_resume_for_job_rejects_empty_description():
    job = Job(
        title="Product Manager",
        company="Example Corp",
        description="",
    )

    try:
        generate_resume_for_job(job)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Job description is empty" in str(exc)
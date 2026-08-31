from unittest.mock import patch

from src.job_ingestion.models import Job
from src.job_ingestion.processor import process_best_job


class FakeAdapter:
    def fetch_jobs(self, **kwargs):
        return [
            Job(
                title="Product Manager",
                company="Example Corp",
                location="Pune, India",
                description="Product management and analytics.",
                url="https://example.com/job/1",
            ),
            Job(
                title="Software Engineer",
                company="Example Corp",
                location="Toronto, Canada",
                description="Python backend development.",
                url="https://example.com/job/2",
            ),
        ]


@patch(
    "src.job_ingestion.processor.generate_resume_for_job",
    return_value="output/test.pdf",
)
def test_process_best_job(mock_generate):
    result = process_best_job(
        adapter=FakeAdapter(),
        target_roles=["Product Manager"],
        preferred_locations=["Pune"],
        minimum_score=0,
    )

    assert result is not None
    assert result["job"].title == "Product Manager"
    assert result["score"] > 0
    assert result["pdf_path"] == "output/test.pdf"

    mock_generate.assert_called_once()
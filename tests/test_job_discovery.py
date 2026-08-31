from src.job_discovery import discover_matching_jobs
from src.job_ingestion.models import Job


class FakeAdapter:
    def fetch_jobs(self, **kwargs):
        return [
            Job(
                title="Product Manager",
                company="Example Corp",
                location="Pune, India",
                description=(
                    "Product management, analytics, "
                    "AI and stakeholder management."
                ),
                url="https://example.com/job/1",
                source="greenhouse",
                job_id="1",
            ),
        ]


def test_discover_matching_jobs():
    results = discover_matching_jobs(
        FakeAdapter(),
        min_score=0,
    )

    assert results
    assert results[0].job.title == "Product Manager"
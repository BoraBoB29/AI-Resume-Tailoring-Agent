from src.job_ingestion.models import Job
from src.job_ingestion.pipeline import discover_jobs


class FakeAdapter:
    def fetch_jobs(self, **kwargs):
        return [
            Job(
                title="Product Manager",
                company="Example Corp",
                location="Pune, India",
                description="Product management and analytics",
                url="https://example.com/job/1",
                source="greenhouse",
                job_id="1",
            ),
            Job(
                title="Software Engineer",
                company="Example Corp",
                location="Toronto, Canada",
                description="Python backend development",
                url="https://example.com/job/2",
                source="greenhouse",
                job_id="2",
            ),
        ]


def test_discover_jobs_returns_jobs():
    results = discover_jobs(
        adapter=FakeAdapter(),
        target_roles=["Product Manager"],
        preferred_locations=["Pune"],
    )

    assert len(results) >= 1
    assert results[0].title == "Product Manager"
import httpx
import pytest

from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter


def make_client(payload, status_code=200):
    def handler(request):
        return httpx.Response(
            status_code=status_code,
            json=payload,
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_fetch_jobs_normalizes_greenhouse_response():
    payload = {
        "jobs": [
            {
                "id": 123,
                "title": "Product Manager",
                "company_name": "TestCompany",
                "location": {"name": "Pune, India"},
                "content": "<p>Manage product roadmap.</p>",
                "absolute_url": "https://example.com/jobs/123",
            }
        ]
    }

    adapter = GreenhouseAdapter(
        "test-company",
        client=make_client(payload),
    )

    jobs = adapter.fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].title == "Product Manager"
    assert jobs[0].company == "TestCompany"
    assert jobs[0].location == "Pune, India"
    assert jobs[0].source == "greenhouse"
    assert jobs[0].job_id == "123"
    assert jobs[0].url == "https://example.com/jobs/123"


def test_fetch_jobs_empty_response():
    adapter = GreenhouseAdapter(
        "test-company",
        client=make_client({"jobs": []}),
    )

    assert adapter.fetch_jobs() == []


def test_fetch_jobs_http_error():
    adapter = GreenhouseAdapter(
        "test-company",
        client=make_client({"error": "bad"}, status_code=500),
    )

    with pytest.raises(RuntimeError, match="HTTP 500"):
        adapter.fetch_jobs()


def test_fetch_jobs_request_error():
    def handler(request):
        raise httpx.ConnectError("connection failed")

    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )

    adapter = GreenhouseAdapter(
        "test-company",
        client=client,
    )

    with pytest.raises(RuntimeError, match="request failed"):
        adapter.fetch_jobs()


def test_fetch_jobs_skips_non_object_items():
    adapter = GreenhouseAdapter(
        "test-company",
        client=make_client({
            "jobs": [
                None,
                "invalid",
            ]
        }),
    )

    assert adapter.fetch_jobs() == []


def test_fetch_job_detail():
    payload = {
        "id": 999,
        "title": "Data Analyst",
        "company_name": "TestCompany",
        "location": {"name": "Remote"},
        "content": "<p>Analyze data.</p>",
        "absolute_url": "https://example.com/jobs/999",
    }

    def handler(request):
        assert request.url.path.endswith("/jobs/999")
        return httpx.Response(
            200,
            json=payload,
            request=request,
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )

    adapter = GreenhouseAdapter(
        "test-company",
        client=client,
    )

    job = adapter.fetch_job_detail(999)

    assert job.title == "Data Analyst"
    assert job.company == "TestCompany"
    assert job.job_id == "999"
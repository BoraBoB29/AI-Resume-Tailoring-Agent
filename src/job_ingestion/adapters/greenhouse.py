from __future__ import annotations

from html import unescape

from src.job_ingestion.adapters.base import JobSourceAdapter
from src.job_ingestion.models import Job
from src.job_ingestion.normalizer import normalize_job


class GreenhouseAdapter(JobSourceAdapter):
    """
    Adapter for the public Greenhouse Job Board API.

    Example:
        https://boards-api.greenhouse.io/v1/boards/examplecorpsandbox/jobs?content=true
    """

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(self, http_client=None):
        self.http_client = http_client

    def fetch_jobs(
        self,
        board: str,
        content: bool = True,
        **kwargs,
    ) -> list[Job]:
        if not board:
            raise ValueError("Greenhouse board name is required.")

        url = f"{self.BASE_URL}/{board}/jobs"

        params = {
            "content": str(content).lower(),
        }

        if self.http_client is not None:
            response = self.http_client.get(url, params=params, timeout=20)
            data = response.json()
        else:
            import requests

            response = requests.get(
                url,
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()

        jobs = data.get("jobs", [])

        return [
            self._normalize_greenhouse_job(job)
            for job in jobs
        ]

    def _normalize_greenhouse_job(self, data: dict) -> Job:
        location = data.get("location") or {}

        raw_description = data.get("content", "")
        description = unescape(raw_description)

        normalized = {
            "title": data.get("title", ""),
            "company": data.get("company_name", ""),
            "location": location.get("name", ""),
            "description": description,
            "url": data.get("absolute_url"),
            "source": "greenhouse",
            "job_id": str(data.get("id", "")),
            "requirements": [],
            "skills": [],
            "raw_data": data,
        }

        return normalize_job(normalized)
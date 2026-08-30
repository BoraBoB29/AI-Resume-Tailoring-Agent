from __future__ import annotations

from typing import Any

import httpx

from src.job_ingestion.adapters.base import JobSourceAdapter
from src.job_ingestion.models import Job
from src.job_ingestion.normalizer import normalize_job


class GreenhouseAdapter(JobSourceAdapter):
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(
        self,
        board_token: str,
        *,
        timeout: float = 15.0,
        client: httpx.Client | None = None,
    ) -> None:
        if not board_token or not board_token.strip():
            raise ValueError("Greenhouse board token is required.")

        self.board_token = board_token.strip()
        self.timeout = timeout
        self._client = client

    def fetch_jobs(self, **kwargs: Any) -> list[Job]:
        url = f"{self.BASE_URL}/{self.board_token}/jobs"

        client = self._client or httpx.Client(timeout=self.timeout)

        should_close = self._client is None

        try:
            response = client.get(url)
            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError("Greenhouse response must be a JSON object.")

            jobs = payload.get("jobs", [])

            if not isinstance(jobs, list):
                raise ValueError("Greenhouse 'jobs' field must be a list.")

            results: list[Job] = []

            for raw_job in jobs:
                if not isinstance(raw_job, dict):
                    continue

                results.append(self._normalize_greenhouse_job(raw_job))

            return results

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Greenhouse API returned HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Greenhouse API request failed: {exc}"
            ) from exc

        finally:
            if should_close:
                client.close()

    def fetch_job_detail(self, job_id: str | int) -> Job:
        url = f"{self.BASE_URL}/{self.board_token}/jobs/{job_id}"

        client = self._client or httpx.Client(timeout=self.timeout)

        should_close = self._client is None

        try:
            response = client.get(url)
            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError("Greenhouse job detail must be a JSON object.")

            return self._normalize_greenhouse_job(payload)

        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Greenhouse API returned HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Greenhouse API request failed: {exc}"
            ) from exc

        finally:
            if should_close:
                client.close()

    @staticmethod
    def _normalize_greenhouse_job(raw_job: dict[str, Any]) -> Job:
        location = raw_job.get("location")

        if isinstance(location, dict):
            location_value = location.get("name")
        else:
            location_value = location

        content = raw_job.get("content", "")

        return normalize_job(
            {
                "title": raw_job.get("title", ""),
                "company": raw_job.get("company_name", ""),
                "location": location_value,
                "description": content,
                "url": raw_job.get("absolute_url"),
                "source": "greenhouse",
                "job_id": str(raw_job.get("id", "")),
            }
        )
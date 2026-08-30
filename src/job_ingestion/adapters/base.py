from abc import ABC, abstractmethod

from src.job_ingestion.models import Job


class JobSourceAdapter(ABC):

    @abstractmethod
    def fetch_jobs(self, **kwargs) -> list[Job]:
        """Fetch jobs from a specific source."""
        raise NotImplementedError
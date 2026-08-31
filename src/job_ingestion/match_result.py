from dataclasses import dataclass, field

from src.job_ingestion.models import Job


@dataclass
class JobMatch:
    job: Job
    score: float
    matched_terms: list[str] = field(default_factory=list)
    missing_terms: list[str] = field(default_factory=list)
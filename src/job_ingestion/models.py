from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Job:
    title: str
    company: str
    location: Optional[str] = None
    description: str = ""
    url: Optional[str] = None

    source: Optional[str] = None
    job_id: Optional[str] = None

    employment_type: Optional[str] = None
    workplace_type: Optional[str] = None

    salary: Optional[str] = None

    requirements: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)

    raw_data: dict = field(default_factory=dict)
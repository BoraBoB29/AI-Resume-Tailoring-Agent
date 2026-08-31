from unittest.mock import patch

import pytest

from src.job_ingestion.models import Job
from src.job_ingestion.resume_bridge import generate_resume_for_job


def test_generate_resume_for_job_passes_job_data():
    job = Job(
        title="Product Manager",
        company="Example Corp",
        location="Pune, India",
        description="Build and manage digital products.",
        url="https://example.com/job/1",
    )

    with patch(
        "src.job_ingestion.resume_bridge.generate_resume",
        return_value="output.pdf",
    ) as mock_generate:

        result = generate_resume_for_job(
            job,
            master_resume_path="data/master_resume.yaml",
            max_iterations=2,
        )

    assert result == "output.pdf"

    mock_generate.assert_called_once_with(
        job_description="Build and manage digital products.",
        company="Example Corp",
        role="Product Manager",
        master_resume_path="data/master_resume.yaml",
        strict_one_page=True,
        max_iterations=2,
    )


def test_generate_resume_for_job_rejects_empty_description():
    job = Job(
        title="Product Manager",
        company="Example Corp",
        description="",
    )

    with pytest.raises(ValueError):
        generate_resume_for_job(job)
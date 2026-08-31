from pathlib import Path

from src.job_ingestion.preferences import load_job_preferences


def test_load_job_preferences(tmp_path: Path):
    config = tmp_path / "preferences.yaml"

    config.write_text(
        """
target_roles:
  - Product Manager
  - Product Owner

preferred_locations:
  - Pune
  - Remote

required_terms:
  - Python

minimum_score: 60
""",
        encoding="utf-8",
    )

    preferences = load_job_preferences(config)

    assert preferences.target_roles == [
        "Product Manager",
        "Product Owner",
    ]

    assert preferences.preferred_locations == [
        "Pune",
        "Remote",
    ]

    assert preferences.required_terms == ["Python"]

    assert preferences.minimum_score == 60
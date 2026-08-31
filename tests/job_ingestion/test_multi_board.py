from src.job_ingestion.multi_board import discover_from_greenhouse_boards


def test_discover_from_greenhouse_boards():
    results = discover_from_greenhouse_boards(
        target_roles=["Marketing"],
        minimum_score=50,
        config_path="data/greenhouse_boards.json",
    )

    assert results
    assert results[0].score >= 50
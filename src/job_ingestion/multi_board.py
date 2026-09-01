from __future__ import annotations

from src.job_ingestion.board_config import load_greenhouse_boards
from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter
from src.job_matcher import score_job


def discover_from_greenhouse_boards(
    target_roles=None,
    preferred_locations=None,
    required_terms=None,
    minimum_score=50.0,
    config_path="data/greenhouse_boards.json",
):
    """
    Discover and rank jobs across multiple Greenhouse boards.

    Invalid/unavailable boards are skipped so that one bad board
    does not stop discovery from all other boards.
    """

    boards = load_greenhouse_boards(config_path)

    adapter = GreenhouseAdapter()

    results = []

    for board_config in boards:
        board_name = board_config["name"]
        board_token = board_config["token"]

        print(
            f"Checking Greenhouse board: "
            f"{board_name} ({board_token})"
        )

        try:
            jobs = adapter.fetch_jobs(
                board=board_token,
            )

        except Exception as exc:
            print(
                f"WARNING: Could not load board "
                f"'{board_name}' ({board_token}): {exc}"
            )
            print("Skipping this board and continuing...\n")
            continue

        print(
            f"  Loaded {len(jobs)} jobs from {board_name}."
        )

        for job in jobs:
            result = score_job(
                job,
                target_roles=target_roles or [],
                preferred_locations=preferred_locations or [],
                required_terms=required_terms or [],
            )

            if result.score >= minimum_score:
                results.append(result)

    return sorted(
        results,
        key=lambda result: result.score,
        reverse=True,
    )
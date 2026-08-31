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
    Discover and rank jobs across all enabled Greenhouse boards.
    """

    boards = load_greenhouse_boards(config_path)
    adapter = GreenhouseAdapter()

    results = []

    for board_config in boards:
        token = board_config["token"]

        jobs = adapter.fetch_jobs(
            board=token,
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

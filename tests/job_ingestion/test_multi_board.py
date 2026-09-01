from src.job_ingestion.multi_board import discover_from_greenhouse_boards


def test_discover_from_greenhouse_boards():
    results = discover_from_greenhouse_boards(
        target_roles=["Marketing"],
        minimum_score=50,
        config_path="data/greenhouse_boards.json",
    )

    assert results
    assert results[0].score >= 50


def test_multi_board_skips_invalid_board(tmp_path):
    config = tmp_path / "greenhouse_boards.json"

    config.write_text(
        """
        {
          "boards": [
            {
              "name": "Invalid Board",
              "token": "companytwoboard",
              "enabled": true
            },
            {
              "name": "Example Corp",
              "token": "examplecorpsandbox",
              "enabled": true
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    results = discover_from_greenhouse_boards(
        target_roles=["Marketing"],
        minimum_score=50,
        config_path=config,
    )

    assert results
    assert results[0].job.company == "Example Corp"
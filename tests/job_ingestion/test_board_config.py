import json

from src.job_ingestion.board_config import load_greenhouse_boards


def test_load_greenhouse_boards(tmp_path):
    config = {
        "boards": [
            {
                "name": "Example Corp",
                "token": "examplecorpsandbox",
                "enabled": True,
            },
            {
                "name": "Disabled Corp",
                "token": "disabled",
                "enabled": False,
            },
        ]
    }

    config_path = tmp_path / "boards.json"

    config_path.write_text(
        json.dumps(config),
        encoding="utf-8",
    )

    boards = load_greenhouse_boards(config_path)

    assert len(boards) == 1
    assert boards[0]["name"] == "Example Corp"
    assert boards[0]["token"] == "examplecorpsandbox"
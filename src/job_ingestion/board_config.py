from __future__ import annotations

import json
from pathlib import Path


DEFAULT_CONFIG_PATH = Path("data/greenhouse_boards.json")


def load_greenhouse_boards(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
) -> list[dict]:
    """
    Load enabled Greenhouse boards from configuration.

    Expected JSON format:

    {
        "boards": [
            {
                "name": "Example Corp",
                "token": "examplecorpsandbox",
                "enabled": true
            }
        ]
    }
    """

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Greenhouse board configuration not found: {path}"
        )

    # utf-8-sig handles both normal UTF-8 and UTF-8 files containing a BOM.
    with path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Greenhouse board configuration must be a JSON object.")

    boards = data.get("boards", [])

    if not isinstance(boards, list):
        raise ValueError("'boards' must be a list.")

    enabled_boards = []

    for board in boards:
        if not isinstance(board, dict):
            continue

        if not board.get("enabled", True):
            continue

        token = str(
            board.get("token", board.get("board", ""))
        ).strip()

        if not token:
            continue

        enabled_boards.append(
            {
                "name": str(
                    board.get("name", token)
                ).strip(),
                "token": token,
            }
        )

    return enabled_boards
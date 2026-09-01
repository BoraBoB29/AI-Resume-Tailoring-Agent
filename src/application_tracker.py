from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_APPLICATION_PATH = Path(
    "data/jobs/applications.json"
)


VALID_STATUSES = {
    "DISCOVERED",
    "REVIEWED",
    "SELECTED",
    "RESUME_GENERATED",
    "READY_TO_APPLY",
    "APPLIED",
    "INTERVIEW",
    "OFFER",
    "REJECTED",
}


def _load(
    path: str | Path = DEFAULT_APPLICATION_PATH,
) -> dict:

    path = Path(path)

    if not path.exists():
        return {"applications": []}

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _save(
    data: dict,
    path: str | Path = DEFAULT_APPLICATION_PATH,
) -> None:

    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def create_application(
    job_id: str,
    title: str,
    company: str,
    url: str | None = None,
    status: str = "DISCOVERED",
    path: str | Path = DEFAULT_APPLICATION_PATH,
) -> dict:

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}"
        )

    data = _load(path)

    for application in data["applications"]:
        if application["job_id"] == job_id:
            return application

    now = datetime.now(
        timezone.utc
    ).isoformat()

    application = {
        "job_id": job_id,
        "title": title,
        "company": company,
        "url": url,
        "status": status,
        "created_at": now,
        "updated_at": now,
    }

    data["applications"].append(
        application
    )

    _save(data, path)

    return application


def update_status(
    job_id: str,
    status: str,
    path: str | Path = DEFAULT_APPLICATION_PATH,
) -> dict:

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {status}"
        )

    data = _load(path)

    for application in data["applications"]:

        if application["job_id"] == job_id:

            application["status"] = status

            application["updated_at"] = (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )

            _save(data, path)

            return application

    raise KeyError(
        f"Application not found: {job_id}"
    )


def list_applications(
    path: str | Path = DEFAULT_APPLICATION_PATH,
) -> list[dict]:

    data = _load(path)

    return data["applications"]
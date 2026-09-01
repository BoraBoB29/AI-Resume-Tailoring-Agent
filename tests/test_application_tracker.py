from src.application_tracker import (
    create_application,
    update_status,
    list_applications,
)


def test_create_application(tmp_path):

    path = tmp_path / "applications.json"

    application = create_application(
        job_id="123",
        title="Product Manager",
        company="Example Corp",
        url="https://example.com/job/123",
        path=path,
    )

    assert application["job_id"] == "123"
    assert application["status"] == "DISCOVERED"


def test_update_application_status(tmp_path):

    path = tmp_path / "applications.json"

    create_application(
        job_id="123",
        title="Product Manager",
        company="Example Corp",
        path=path,
    )

    application = update_status(
        job_id="123",
        status="READY_TO_APPLY",
        path=path,
    )

    assert application["status"] == "READY_TO_APPLY"


def test_list_applications(tmp_path):

    path = tmp_path / "applications.json"

    create_application(
        job_id="123",
        title="Product Manager",
        company="Example Corp",
        path=path,
    )

    applications = list_applications(path)

    assert len(applications) == 1
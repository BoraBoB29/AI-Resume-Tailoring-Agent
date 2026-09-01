import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.application_tracker import (
    create_application,
    update_status,
    list_applications,
)


def main():

    parser = argparse.ArgumentParser(
        description="Track job applications."
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    create_parser = subparsers.add_parser(
        "create"
    )

    create_parser.add_argument(
        "--job-id",
        required=True,
    )

    create_parser.add_argument(
        "--title",
        required=True,
    )

    create_parser.add_argument(
        "--company",
        required=True,
    )

    create_parser.add_argument(
        "--url",
        default=None,
    )

    status_parser = subparsers.add_parser(
        "status"
    )

    status_parser.add_argument(
        "--job-id",
        required=True,
    )

    status_parser.add_argument(
        "--status",
        required=True,
    )

    subparsers.add_parser(
        "list"
    )

    args = parser.parse_args()

    if args.command == "create":

        application = create_application(
            job_id=args.job_id,
            title=args.title,
            company=args.company,
            url=args.url,
        )

        print(
            f"Created application: "
            f"{application['title']} "
            f"at {application['company']}"
        )

        return

    if args.command == "status":

        application = update_status(
            job_id=args.job_id,
            status=args.status,
        )

        print(
            f"{application['job_id']} "
            f"-> {application['status']}"
        )

        return

    if args.command == "list":

        applications = list_applications()

        if not applications:
            print("No applications found.")
            return

        for application in applications:

            print(
                f"{application['job_id']} | "
                f"{application['title']} | "
                f"{application['company']} | "
                f"{application['status']}"
            )


if __name__ == "__main__":
    main()
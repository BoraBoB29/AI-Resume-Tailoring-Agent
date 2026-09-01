import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.job_store import load_matches
from src.job_matcher import JobMatchResult
from src.job_ingestion.models import Job
from src.application_package import prepare_application
from src.application_tracker import create_application


def reconstruct_match(data: dict) -> JobMatchResult:
    """
    Reconstruct a JobMatchResult from job_store.json.
    """

    job_data = data["job"]

    job = Job(
        title=job_data["title"],
        company=job_data["company"],
        location=job_data.get("location"),
        description=job_data.get(
            "description",
            "",
        ),
        url=job_data.get("url"),
        source=job_data.get(
            "source",
            "unknown",
        ),
        job_id=job_data.get(
            "job_id"
        ),
        employment_type=job_data.get(
            "employment_type"
        ),
        workplace_type=job_data.get(
            "workplace_type"
        ),
        salary=job_data.get(
            "salary"
        ),
        requirements=job_data.get(
            "requirements",
            [],
        ),
        skills=job_data.get(
            "skills",
            [],
        ),
        raw_data=job_data.get(
            "raw_data",
            {},
        ),
    )

    return JobMatchResult(
        job=job,
        score=data["score"],
        matched_terms=data.get(
            "matched_terms",
            [],
        ),
        missing_terms=data.get(
            "missing_terms",
            [],
        ),
    )


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Prepare a complete application "
            "package from a stored job."
        )
    )

    parser.add_argument(
        "--index",
        type=int,
        required=True,
        help=(
            "1-based job index from "
            "job_store.json."
        ),
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    matches = load_matches()

    if not matches:
        print(
            "No stored jobs found."
        )
        print(
            "Run job discovery first."
        )
        return

    if args.index < 1 or args.index > len(matches):
        print(
            f"Index must be between "
            f"1 and {len(matches)}."
        )
        return

    match = reconstruct_match(
        matches[args.index - 1]
    )

    job = match.job

    print("\nSelected job:")
    print(
        f"Title:    {job.title}"
    )
    print(
        f"Company:  {job.company}"
    )
    print(
        f"Location: {job.location}"
    )
    print(
        f"Score:    {match.score}"
    )
    print(
        f"URL:      {job.url}"
    )

    confirm = input(
        "\nPrepare application package? [y/N]: "
    ).strip().lower()

    if confirm != "y":
        print("Cancelled.")
        return

    result = prepare_application(
        match,
        max_iterations=args.max_iterations,
    )

    create_application(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        url=job.url,
        status="READY_TO_APPLY",
    )

    print(
        "\n================================"
    )
    print(
        "APPLICATION PACKAGE READY"
    )
    print(
        "================================"
    )

    print(
        f"Directory:     {result['directory']}"
    )

    print(
        f"Resume:        {result['resume']}"
    )

    print(
        f"Cover Letter:  {result['cover_letter']}"
    )

    print(
        f"Metadata:      {result['metadata']}"
    )

    print(
        "\nStatus: READY_TO_APPLY"
    )


if __name__ == "__main__":
    main()
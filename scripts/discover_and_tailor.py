import argparse

from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter
from src.job_matcher import filter_jobs
from src.job_resume_pipeline import generate_resume_for_job


def main():
    parser = argparse.ArgumentParser(
        description="Discover Greenhouse jobs, rank them, and tailor a resume."
    )

    parser.add_argument(
        "--board",
        required=True,
        help="Greenhouse board token.",
    )

    parser.add_argument(
        "--role",
        action="append",
        required=True,
        help="Target role. Can be supplied multiple times.",
    )

    parser.add_argument(
        "--location",
        action="append",
        default=[],
        help="Preferred location. Can be supplied multiple times.",
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=50.0,
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    adapter = GreenhouseAdapter(board_token=args.board)

    jobs = adapter.fetch_jobs()

    print(f"\nDiscovered {len(jobs)} jobs.")

    matches = filter_jobs(
        jobs,
        target_roles=args.role,
        preferred_locations=args.location,
        minimum_score=args.min_score,
    )

    print(f"Matching jobs: {len(matches)}")

    if not matches:
        print("No jobs met the minimum score.")
        return

    print("\nTop matches:")

    for index, result in enumerate(matches[:10], start=1):
        print(
            f"{index}. "
            f"{result.job.title} | "
            f"{result.job.company} | "
            f"{result.job.location} | "
            f"Score: {result.score}"
        )

    best = matches[0]

    print("\nSelected job:")
    print(f"Title: {best.job.title}")
    print(f"Company: {best.job.company}")
    print(f"Location: {best.job.location}")
    print(f"Score: {best.score}")

    pdf_path = generate_resume_for_job(
        best.job,
        max_iterations=args.max_iterations,
    )

    print(f"\nTailored resume ready: {pdf_path}")


if __name__ == "__main__":
    main()
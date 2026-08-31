import argparse

from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter
from src.job_ingestion.processor import process_best_job
from src.job_ingestion.preferences import load_job_preferences


def main():
    parser = argparse.ArgumentParser(
        description="Discover the best job and generate a tailored resume."
    )

    parser.add_argument(
        "--greenhouse-board",
        required=True,
    )

    parser.add_argument(
        "--preferences",
        default="data/job_preferences.yaml",
    )

    parser.add_argument(
        "--master-resume",
        default="data/master_resume.yaml",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
    )

    args = parser.parse_args()

    preferences = load_job_preferences(
        args.preferences
    )

    adapter = GreenhouseAdapter(
        board_token=args.greenhouse_board
    )

    result = process_best_job(
        adapter=adapter,
        target_roles=preferences.target_roles,
        preferred_locations=preferences.preferred_locations,
        required_terms=preferences.required_terms,
        minimum_score=preferences.minimum_score,
        master_resume_path=args.master_resume,
        max_iterations=args.max_iterations,
    )

    if result is None:
        print("No matching jobs found.")
        return

    job = result["job"]

    print("\n========== SELECTED JOB ==========")
    print(f"Title: {job.title}")
    print(f"Company: {job.company}")
    print(f"Location: {job.location}")
    print(f"Score: {result['score']}")
    print(f"URL: {job.url}")

    print("\nMatched terms:")
    for term in result["matched_terms"]:
        print(f"- {term}")

    print("\nMissing terms:")
    for term in result["missing_terms"]:
        print(f"- {term}")

    print("\n========== RESUME ==========")
    print(f"Generated: {result['pdf_path']}")


if __name__ == "__main__":
    main()
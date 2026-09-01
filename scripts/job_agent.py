import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.job_agent import JobAgent
from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter
from src.job_ingestion.multi_board import discover_from_greenhouse_boards
from src.job_store import save_matches

def main():
    parser = argparse.ArgumentParser(
        description="Discover jobs and generate a tailored resume."
    )

    parser.add_argument(
        "--board",
        required=False,
        help="Single Greenhouse board token.",
    )

    parser.add_argument(
        "--all-boards",
        action="store_true",
        help="Search all enabled Greenhouse boards in data/greenhouse_boards.json.",
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
        help="Minimum job match score.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of jobs to display.",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Maximum resume-tailoring iterations.",
    )

    args = parser.parse_args()

    # Require either --board or --all-boards.
    if not args.board and not args.all_boards:
        parser.error("provide either --board BOARD or --all-boards")

    if args.board and args.all_boards:
        parser.error("--board and --all-boards cannot be used together")

    print("\nDiscovering jobs...")

    if args.all_boards:
        matches = discover_from_greenhouse_boards(
            target_roles=args.role,
            preferred_locations=args.location,
            minimum_score=args.min_score,
            config_path="data/greenhouse_boards.json",
        )
    else:
        adapter = GreenhouseAdapter()
        agent = JobAgent(adapter)

        matches = agent.discover(
            target_roles=args.role,
            preferred_locations=args.location,
            minimum_score=args.min_score,
            board=args.board,
        )

    print(f"\nFound {len(matches)} matching jobs.\n")

    if not matches:
        print("No jobs matched your criteria.")
        return

    store_path = save_matches(matches)

    print(f"Saved job matches to: {store_path}")

    displayed = matches[:args.limit]

    for index, result in enumerate(displayed, start=1):
        job = result.job

        print(
            f"{index}. "
            f"{job.title} | "
            f"{job.company} | "
            f"{job.location or 'Unknown'} | "
            f"Score: {result.score}"
        )

    print()

    while True:
        choice = input(
            f"Select a job [1-{len(displayed)}, q to quit]: "
        ).strip()

        if choice.lower() == "q":
            print("Cancelled.")
            return

        try:
            index = int(choice)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if 1 <= index <= len(displayed):
            selected = displayed[index - 1]
            break

        print("Selection out of range.")

    job = selected.job

    print("\nSelected job:")
    print(f"Title:    {job.title}")
    print(f"Company:  {job.company}")
    print(f"Location: {job.location}")
    print(f"URL:      {job.url}")
    print(f"Score:    {selected.score}")

    if selected.matched_terms:
        print(f"Matched:  {', '.join(selected.matched_terms)}")

    if selected.missing_terms:
        print(f"Missing:  {', '.join(selected.missing_terms)}")

    confirm = input(
        "\nGenerate tailored resume? [y/N]: "
    ).strip().lower()

    if confirm != "y":
        print("Cancelled.")
        return

    print("\nGenerating tailored resume...\n")

    agent = JobAgent(GreenhouseAdapter())

    pdf_path = agent.generate_resume(
        selected,
        max_iterations=args.max_iterations,
    )

    print(f"\nResume ready: {pdf_path}")


if __name__ == "__main__":
    main()

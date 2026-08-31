import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
from src.job_agent import JobAgent
from src.job_ingestion.adapters.greenhouse import GreenhouseAdapter


def main():
    parser = argparse.ArgumentParser(
        description="Discover jobs and generate a tailored resume."
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
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    print("\nDiscovering jobs...")

    adapter = GreenhouseAdapter(
        board_token=args.board,
    )

    agent = JobAgent(adapter)

    matches = agent.discover(
        target_roles=args.role,
        preferred_locations=args.location,
        minimum_score=args.min_score,
    )

    print(f"\nFound {len(matches)} matching jobs.\n")

    if not matches:
        print("No jobs matched your criteria.")
        return

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

    confirm = input(
        "\nGenerate tailored resume? [y/N]: "
    ).strip().lower()

    if confirm != "y":
        print("Cancelled.")
        return

    print("\nGenerating tailored resume...\n")

    pdf_path = agent.generate_resume(
        selected,
        max_iterations=args.max_iterations,
    )

    print(f"\nResume ready: {pdf_path}")


if __name__ == "__main__":
    main()
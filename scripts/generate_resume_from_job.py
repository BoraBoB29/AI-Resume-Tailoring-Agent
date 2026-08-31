import argparse

from src.job_ingestion.models import Job
from src.job_resume_pipeline import generate_resume_for_job


def main():
    parser = argparse.ArgumentParser(
        description="Generate a tailored resume from a normalized job."
    )

    parser.add_argument("--title", required=True)
    parser.add_argument("--company", required=True)
    parser.add_argument("--description-file", required=True)
    parser.add_argument("--location", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--max-iterations", type=int, default=None)
    parser.add_argument("--allow-multi-page", action="store_true")

    args = parser.parse_args()

    with open(args.description_file, "r", encoding="utf-8") as f:
        description = f.read()

    job = Job(
        title=args.title,
        company=args.company,
        location=args.location or None,
        description=description,
        url=args.url or None,
        source=args.source or None,
        job_id=args.job_id or None,
    )

    pdf_path = generate_resume_for_job(
        job,
        max_iterations=args.max_iterations,
        strict_one_page=not args.allow_multi_page,
    )

    print(f"\nResume ready: {pdf_path}")


if __name__ == "__main__":
    main()
"""
Phase 1 CLI: generate a tailored, LaTeX-compiled PDF resume from a job description.

Usage examples:
    python main.py --jd-file path/to/jd.txt --company "Acme" --role "Backend Engineer"
    python main.py --jd "Paste the job description text directly here..."
"""
import argparse
import sys

from src.resume_generator import generate_resume


def main():
    parser = argparse.ArgumentParser(description="Generate a tailored resume PDF from a job description.")
    jd_group = parser.add_mutually_exclusive_group(required=True)
    jd_group.add_argument("--jd", type=str, help="Job description text, passed directly.")
    jd_group.add_argument("--jd-file", type=str, help="Path to a .txt file containing the job description.")

    parser.add_argument("--company", type=str, default="", help="Company name (used for output filename).")
    parser.add_argument("--role", type=str, default="", help="Role/title (used for output filename).")
    parser.add_argument(
        "--master-resume", type=str, default=None,
        help="Path to master resume YAML (default: data/master_resume.yaml)."
    )

    args = parser.parse_args()

    if args.jd_file:
        with open(args.jd_file, "r", encoding="utf-8") as f:
            job_description = f.read()
    else:
        job_description = args.jd

    try:
        pdf_path = generate_resume(
            job_description=job_description,
            company=args.company,
            role=args.role,
            master_resume_path=args.master_resume,
        )
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\nResume ready: {pdf_path}")


if __name__ == "__main__":
    main()

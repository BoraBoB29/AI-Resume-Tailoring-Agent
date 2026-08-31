from src.job_discovery import discover_matching_jobs


def run_discovery(adapter):
    results = discover_matching_jobs(adapter)

    print()
    print("========== MATCHING JOBS ==========")

    for index, result in enumerate(results, start=1):
        job = result.job

        print(
            f"{index}. {job.title} | "
            f"{job.company} | "
            f"{job.location or 'Unknown'}"
        )

        print(f"   Score: {result.score:.1f}")

        if result.matched_terms:
            print(
                "   Matched: "
                + ", ".join(result.matched_terms)
            )

        if result.missing_terms:
            print(
                "   Missing: "
                + ", ".join(result.missing_terms)
            )

        print(f"   URL: {job.url}")
        print()
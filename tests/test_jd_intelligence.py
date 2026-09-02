from src.jd_intelligence import analyze_candidate_against_job


def test_jd_intelligence_pipeline():
    jd = """
    Product Manager required.
    4+ years of experience.
    Strong project management and SQL skills.
    SaaS experience is preferred.
    """

    resume = """
    Product management experience.
    Led project management initiatives.
    Python automation.
    """

    result = analyze_candidate_against_job(
        job_description=jd,
        resume_text=resume,
    )

    assert result.analysis.required
    assert result.ats_score.overall_score >= 0
    assert result.gaps

    missing = [
        gap.requirement.lower()
        for gap in result.gaps
    ]

    assert "sql" in missing
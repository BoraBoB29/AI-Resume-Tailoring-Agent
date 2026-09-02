from src.ats_scorer import (
    ATSScore,
    score_keyword_coverage,
    print_ats_score,
)


def test_score_keyword_coverage_matches_required_keywords():
    resume = """
    Product Manager with experience in Python, SQL,
    analytics, product strategy, and stakeholder management.
    """

    result = score_keyword_coverage(
        resume,
        required_keywords=[
            "Product Manager",
            "Python",
            "SQL",
        ],
        preferred_keywords=[
            "analytics",
        ],
    )

    assert isinstance(result, ATSScore)
    assert result.required_score == 100.0
    assert result.preferred_score == 100.0
    assert result.overall_score == 100.0

    assert "Product Manager" in result.matched
    assert "Python" in result.matched
    assert "SQL" in result.matched
    assert "analytics" in result.matched

    assert result.missing == []


def test_score_keyword_coverage_identifies_missing_keywords():
    resume = """
    Product Manager with experience in Python and SQL.
    """

    result = score_keyword_coverage(
        resume,
        required_keywords=[
            "Product Manager",
            "Python",
            "Java",
        ],
        preferred_keywords=[
            "AWS",
        ],
    )

    assert result.required_score == 66.66666666666666
    assert result.preferred_score == 0.0

    assert "Product Manager" in result.matched
    assert "Python" in result.matched

    assert "Java" in result.missing
    assert "AWS" in result.missing


def test_score_keyword_coverage_empty_keywords():
    result = score_keyword_coverage(
        "Product Manager with Python experience.",
        required_keywords=[],
        preferred_keywords=[],
    )

    assert isinstance(result, ATSScore)
    assert result.required_score == 100.0
    assert result.preferred_score == 100.0
    assert result.overall_score == 100.0
    assert result.matched == []
    assert result.missing == []


def test_score_resume_alias():
    from src.ats_scorer import score_resume

    result = score_resume(
        "Product Manager with Python experience.",
        required_keywords=["Product Manager"],
        preferred_keywords=["Python"],
    )

    assert isinstance(result, ATSScore)
    assert result.overall_score == 100.0


def test_print_ats_score(capsys):
    score = ATSScore(
        required_score=80.0,
        preferred_score=50.0,
        overall_score=70.0,
        matched=["Python"],
        missing=["SQL"],
    )

    print_ats_score(score)

    output = capsys.readouterr().out

    assert "ATS SCORE" in output
    assert "80.00%" in output
    assert "50.00%" in output
    assert "70.00%" in output
    assert "Python" in output
    assert "SQL" in output
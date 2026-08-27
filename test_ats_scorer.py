import pytest

from src.ats_scorer import ATSScore, score_keyword_coverage
from src.schema import JDRequirement


@pytest.fixture
def resume():
    return {
        "summary": "Python analyst building Power BI reports.",
        "skills": {"categories": {"Languages": ["SQL", "Python"], "Tools": ["Power BI"]}},
        "experience": [{"company": "Example Co", "title": "Analyst", "bullets": ["Built SQL dashboards"]}],
        "projects": [{"name": "Forecast", "tech_stack": ["Pandas"], "bullets": ["Created reports"]}],
        "education": [{"degree": "Bachelor of Engineering", "institution": "Example University", "details": []}],
        "certifications": [{"name": "Google Data Analytics Certificate", "issuer": "Coursera"}],
    }


def requirement(name, level="required"):
    return JDRequirement(requirement=name, evidence_level=level)


def test_exact_keyword_match(resume):
    score = score_keyword_coverage(resume, [requirement("SQL")])

    assert score.matched_keywords == ["SQL"]
    assert score.coverage_pct == 100.0


def test_matching_is_case_insensitive(resume):
    assert score_keyword_coverage(resume, [requirement("python")]).coverage_pct == 100.0


def test_missing_required_keyword(resume):
    score = score_keyword_coverage(resume, [requirement("Tableau")])

    assert score.required_missing == 1
    assert score.missing_keywords == ["Tableau"]
    assert score.coverage_pct == 0.0


def test_missing_preferred_keyword(resume):
    score = score_keyword_coverage(resume, [requirement("R", "preferred")])

    assert score.preferred_missing == 1
    assert score.coverage_pct == 0.0


def test_multiple_matches_and_required_preferred_breakdown(resume):
    score = score_keyword_coverage(resume, [
        requirement("SQL"), requirement("Power BI"), requirement("Tableau", "preferred"),
    ])

    assert score.required_matched == 2
    assert score.required_missing == 0
    assert score.preferred_matched == 0
    assert score.preferred_missing == 1
    assert score.coverage_pct == round(2 * 100 / 3, 2)


def test_power_bi_spacing_normalization(resume):
    resume["skills"]["categories"]["Tools"] = ["PowerBI"]

    assert score_keyword_coverage(resume, [requirement("Power BI")]).coverage_pct == 100.0


def test_duplicate_keywords_are_reported_once(resume):
    score = score_keyword_coverage(resume, [requirement("SQL"), requirement("SQL")])

    assert score.matched_keywords == ["SQL"]
    assert score.required_matched == 1


def test_implicit_requirements_are_reported_separately(resume):
    score = score_keyword_coverage(resume, [requirement("Python", "implicit")])

    assert score.coverage_pct == 0.0
    assert score.implicit_matched == ["Python"]
    assert score.matched_keywords == []


def test_empty_requirements_and_resume():
    assert score_keyword_coverage({}, []).model_dump() == ATSScore().model_dump()
    assert score_keyword_coverage({}, [requirement("SQL")]).missing_keywords == ["SQL"]


def test_punctuation_and_whitespace_normalization(resume):
    assert score_keyword_coverage(resume, [requirement("  power   bi ")]).coverage_pct == 100.0


def test_false_positive_is_not_created(resume):
    resume["summary"] = "Jira-like workflow exposure"

    assert score_keyword_coverage(resume, [requirement("Jira")]).missing_keywords == ["Jira"]


def test_repeated_scoring_is_deterministic(resume):
    requirements = [requirement("SQL"), requirement("Tableau", "preferred")]

    assert score_keyword_coverage(resume, requirements) == score_keyword_coverage(resume, requirements)


def test_accepts_requirement_dictionaries(resume):
    score = score_keyword_coverage(resume, [{"requirement": "SQL", "evidence_level": "required"}])

    assert score.required_matched == 1

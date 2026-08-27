import pytest

from src.evidence_matcher import match_evidence
from src.schema import JDRequirement


@pytest.fixture
def master_resume():
    return {
        "skills": {
            "categories": {
                "Data Analytics": ["SQL", "Power BI"],
                "Languages": ["Python"],
            }
        },
        "experience": [
            {"company": "Example Co", "bullets": ["Built SQL dashboards", "Worked with stakeholders"]}
        ],
        "projects": [
            {
                "name": "Sales Forecast",
                "tech_stack": ["SQL", "Pandas"],
                "bullets": ["Created a Power BI dashboard"],
            }
        ],
        "certifications": [{"name": "Google Data Analytics Certificate", "issuer": "Coursera"}],
        "education": [{"institution": "Example University", "degree": "Bachelor of Engineering", "details": []}],
    }


def requirement(text):
    return JDRequirement(
        requirement=text,
        evidence_level="required",
    )


def test_exact_skill_match(master_resume):
    result = match_evidence([requirement("SQL")], master_resume)

    assert result[0].supporting_evidence == [
        "skills.Data Analytics[0]",
        "experience.Example Co.bullets[0]",
        "projects.Sales Forecast.tech_stack[0]",
    ]


def test_experience_bullet_match(master_resume):
    result = match_evidence([requirement("stakeholders")], master_resume)

    assert result[0].supporting_evidence == ["experience.Example Co.bullets[1]"]


def test_project_technology_and_bullet_matches(master_resume):
    result = match_evidence([requirement("Power BI")], master_resume)

    assert result[0].supporting_evidence == [
        "skills.Data Analytics[1]",
        "projects.Sales Forecast.bullets[0]",
    ]


def test_certification_match(master_resume):
    result = match_evidence([requirement("Google Data Analytics")], master_resume)

    assert result[0].supporting_evidence == ["certifications[0]"]


def test_education_match(master_resume):
    result = match_evidence([requirement("engineering degree")], master_resume)

    assert result[0].supporting_evidence == ["education[0]"]


def test_no_evidence_is_empty(master_resume):
    result = match_evidence([requirement("Tableau")], master_resume)

    assert result[0].supporting_evidence == []


def test_matching_is_case_insensitive(master_resume):
    result = match_evidence([requirement("pOwEr bI")], master_resume)

    assert "skills.Data Analytics[1]" in result[0].supporting_evidence


def test_duplicate_evidence_is_removed(master_resume):
    result = match_evidence([requirement("SQL")], master_resume)

    assert len(result[0].supporting_evidence) == len(set(result[0].supporting_evidence))


def test_multiple_requirements_have_independent_sources(master_resume):
    result = match_evidence([requirement("Python"), requirement("Pandas")], master_resume)

    assert result[0].supporting_evidence == ["skills.Languages[0]"]
    assert result[1].supporting_evidence == ["projects.Sales Forecast.tech_stack[1]"]


def test_similar_but_unsupported_requirement_does_not_match(master_resume):
    result = match_evidence([requirement("Java")], master_resume)

    assert result[0].supporting_evidence == []


def test_empty_inputs_return_empty_evidence(master_resume):
    assert match_evidence([], master_resume) == []
    assert match_evidence([requirement("SQL")], {})[0].supporting_evidence == []


def test_references_point_to_fixture_locations(master_resume):
    result = match_evidence([requirement("SQL")], master_resume)
    valid_references = {
        "skills.Data Analytics[0]",
        "experience.Example Co.bullets[0]",
        "projects.Sales Forecast.tech_stack[0]",
    }

    assert set(result[0].supporting_evidence).issubset(valid_references)

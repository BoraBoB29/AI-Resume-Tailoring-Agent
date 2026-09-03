import pytest

from src.llm_tailor import ResumeTailor


@pytest.fixture
def tailor():
    return ResumeTailor.__new__(ResumeTailor)


@pytest.fixture
def master_resume():
    return {
        "contact": {
            "name": "Candidate",
            "email": "candidate@example.com",
            "phone": "555-0100",
            "location": "Pune, India",
            "linkedin": "linkedin.com/in/candidate",
        },
        "education": [
            {
                "institution": "Example University",
                "degree": "B.Tech",
                "location": "Pune",
                "start_date": "2020",
                "end_date": "2024",
                "gpa": "7.5/10",
                "details": ["Class XII: 95.25%"],
            }
        ],
        "skills": {
            "categories": {
                "Languages": ["Python", "SQL"],
                "Tools": ["Git"],
            }
        },
        "experience": [
            {
                "company": "Acme",
                "title": "Analyst",
                "location": "Pune",
                "start_date": "2022",
                "end_date": "2024",
                "bullets": ["Built dashboards", "Automated reports", "Improved data quality", "Presented insights"],
            }
        ],
        "projects": [
            {"name": "Canonical Project", "bullets": ["Built the project", "Documented the result", "Tested the workflow"]},
            {"name": "Second Project", "bullets": ["Analyzed data", "Reported findings"]},
            {"name": "Third Project", "bullets": ["Designed a model", "Validated results"]},
        ],
        "certifications": [
            {"name": "Python Certificate", "issuer": "Example", "category": "Technical"}
        ],
    }


def test_normalize_contact_preserves_canonical_location(tailor, master_resume):
    data = {"contact": {"name": "Tailored", "location": "India"}}

    result = tailor._normalize_contact(data, master_resume)

    assert result["contact"]["name"] == "Tailored"
    assert result["contact"]["email"] == "candidate@example.com"
    assert result["contact"]["location"] == "Pune, India"


def test_normalize_contact_handles_malformed_input(tailor, master_resume):
    result = tailor._normalize_contact({"contact": "invalid"}, master_resume)

    assert result["contact"]["phone"] == "555-0100"
    assert result["contact"]["location"] == "Pune, India"


def test_normalize_education_accepts_dict_and_backfills_missing(tailor, master_resume):
    data = {"education": {"institution": "Example University"}}

    result = tailor._normalize_education(data, master_resume)

    assert len(result["education"]) == 1
    assert result["education"][0]["gpa"] == "7.5/10"
    assert result["education"][0]["details"] == ["Class XII: 95.25%"]


def test_normalize_education_handles_malformed_input(tailor, master_resume):
    result = tailor._normalize_education({"education": "invalid"}, master_resume)

    assert result["education"][0]["institution"] == "Example University"


def test_normalize_skills_supports_categories_and_flat_dicts(tailor, master_resume):
    wrapped = tailor._normalize_skills({"skills": {"categories": {"Data": ["SQL"]}}}, master_resume)
    flat = tailor._normalize_skills({"skills": {"Data": ["SQL"]}}, master_resume)

    assert wrapped["skills"]["categories"]["Data"] == ["SQL"]
    assert flat["skills"]["categories"]["Data"] == ["SQL"]


def test_normalize_skills_falls_back_for_missing_or_malformed(tailor, master_resume):
    for value in (None, "invalid"):
        result = tailor._normalize_skills({"skills": value}, master_resume)
        assert result["skills"]["categories"] == master_resume["skills"]["categories"]


def test_normalize_skills_preserves_canonical_categories_and_items(tailor, master_resume):
    result = tailor._normalize_skills(
        {"skills": {"categories": {"Languages": ["Python"]}}},
        master_resume,
    )

    assert result["skills"]["categories"]["Languages"] == ["Python", "SQL"]


def test_normalize_skills_bounds_categories_and_values(tailor):
    categories = {f"Category {index}": [f"Skill {value}" for value in range(12)] for index in range(10)}
    result = tailor._normalize_skills({"skills": None}, {"skills": {"categories": categories}})

    assert len(result["skills"]["categories"]) <= 6
    assert all(len(values) == 12 for values in result["skills"]["categories"].values())
    assert "Additional Skills" not in result["skills"]["categories"]


def test_normalize_experience_normalizes_bullets_and_missing_fields(tailor):
    data = {"experience": [{"company": "Acme", "bullets": "  Built dashboards  "}, {"company": "Empty"}]}

    result = tailor._normalize_experience(data)

    assert result["experience"][0]["bullets"] == ["Built dashboards"]
    assert result["experience"][1]["bullets"] == []
    assert tailor._normalize_experience({"experience": "invalid"})["experience"] == []


def test_normalize_projects_filters_invalid_names_and_backfills(tailor, master_resume):
    data = {"projects": [{"name": "canonical project", "bullets": ["Custom result"]}, {"name": "Not real"}]}

    result = tailor._normalize_projects(data, master_resume)

    assert [project["name"] for project in result["projects"]] == ["Canonical Project", "Second Project", "Third Project"]
    assert result["projects"][0]["bullets"] == ["Custom result", "Built the project"]


def test_normalize_projects_handles_malformed_input(tailor, master_resume):
    result = tailor._normalize_projects({"projects": "invalid"}, master_resume)

    assert len(result["projects"]) == 3


def test_normalize_projects_backfills_second_canonical_bullet(tailor, master_resume):
    result = tailor._normalize_projects(
        {"projects": [{"name": "Canonical Project", "bullets": ["Custom result"]}]},
        master_resume,
    )

    assert result["projects"][0]["bullets"] == ["Custom result", "Built the project"]


def test_normalize_certifications_supports_strings_and_dicts(tailor, master_resume):
    data = {"certifications": ["Python Certificate", {"name": "Other", "issuer": "Issuer"}]}

    result = tailor._normalize_certifications(data, master_resume)

    assert result["certifications"][0] == master_resume["certifications"][0]
    assert result["certifications"][1]["name"] == "Other"


def test_normalize_certifications_preserves_canonical_when_missing(tailor, master_resume):
    result = tailor._normalize_certifications({}, master_resume)

    assert result["certifications"] == master_resume["certifications"]


def test_experience_content_floor_deduplicates_and_backfills(tailor, master_resume):
    result = {"experience": [{"company": "Acme", "bullets": ["Built dashboards", "Built dashboards"]}]}

    tailor._ensure_experience_content_floor(result, master_resume)

    assert result["experience"][0]["bullets"] == ["Built dashboards", "Automated reports", "Improved data quality", "Presented insights"]


def test_experience_content_floor_uses_main_entry_targets(tailor):
    master = {
        "experience": [
            {"company": "TraceLink Inc.", "bullets": [str(index) for index in range(8)]},
            {"company": "Emotorad (Cycles & E-Bikes)", "bullets": [str(index) for index in range(8)]},
        ]
    }
    result = {"experience": [
        {"company": "TraceLink Inc.", "bullets": []},
        {"company": "Emotorad (Cycles & E-Bikes)", "bullets": []},
    ]}

    tailor._ensure_experience_content_floor(result, master)

    assert len(result["experience"][0]["bullets"]) == 7
    assert len(result["experience"][1]["bullets"]) == 6


def test_project_content_floor_backfills_missing_bullets(tailor, master_resume):
    result = {"projects": [{"name": "Canonical Project", "bullets": ["Custom result"]}]}

    tailor._ensure_project_content_floor(result, master_resume)

    assert result["projects"][0]["bullets"] == ["Custom result", "Built the project"]


def test_project_content_floor_ignores_invalid_project(tailor, master_resume):
    result = {"projects": [{"name": "Not real", "bullets": []}]}

    tailor._ensure_project_content_floor(result, master_resume)

    assert result["projects"][0]["bullets"] == []


def test_normalize_skills_uses_generalized_categories_and_filters_workato(tailor):
    master = {"skills": {"categories": {
        "Technical Skills": ["SQL", "Python", "Workato"],
        "Reporting and Visualization": ["Power BI", "Excel"],
        "Professional Strengths": ["Collaboration", "Communication"],
    }}}
    result = tailor._normalize_skills({"skills": {"categories": {
        "Technical Skills": ["SQL"],
        "Reporting and Visualization": ["Power BI"],
    }}}, master)
    categories = result["skills"]["categories"]
    assert "Technical Skills" not in categories
    assert "Tools & Platforms" in categories
    assert "Reporting & Visualization" in categories
    assert all("Workato".casefold() != value.casefold() for values in categories.values() for value in values)
    assert "Additional Skills" not in categories
    assert len(categories) <= 6

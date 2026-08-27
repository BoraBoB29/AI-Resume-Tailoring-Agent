import json

import pytest

from src.jd_analyzer import extract_requirements
from src.schema import JDRequirement


class FakeMessage:
    def __init__(self, content):
        self.content = content


class FakeResponse:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": FakeMessage(content)})()]


class FakeClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

        self.chat = self

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.content)


def response(requirements):
    return json.dumps({"requirements": requirements})


def requirement(text, level, evidence=None):
    return {
        "requirement": text,
        "evidence_level": level,
        "supporting_evidence": evidence or [],
    }


def test_extracts_required_skills():
    client = FakeClient(response([requirement("SQL", "required")]))

    result = extract_requirements("Must have SQL experience.", client=client)

    assert result == [JDRequirement(requirement="SQL", evidence_level="required")]
    assert client.calls[0]["messages"][1]["content"] == "Must have SQL experience."


def test_extracts_preferred_and_implicit_requirements():
    client = FakeClient(response([
        requirement("Power BI", "preferred"),
        requirement("Cross-functional collaboration", "implicit"),
    ]))

    result = extract_requirements("Work with analytics and product teams.", client=client)

    assert [item.evidence_level for item in result] == ["preferred", "implicit"]


def test_extracts_multiple_requirement_types_and_keeps_evidence():
    client = FakeClient(response([
        requirement("Python", "required", ["Python required"]),
        requirement("Bachelor's degree", "required"),
        requirement("Manufacturing domain knowledge", "implicit"),
        requirement("Tableau", "preferred"),
        requirement("Lead cross-functional projects", "implicit"),
    ]))

    result = extract_requirements("A detailed job description.", client=client)

    assert len(result) == 5
    assert result[0].supporting_evidence == ["Python required"]
    assert {item.requirement for item in result} == {
        "Python", "Bachelor's degree", "Manufacturing domain knowledge",
        "Tableau", "Lead cross-functional projects",
    }


def test_empty_and_very_short_jd_do_not_call_mistral():
    client = FakeClient("unexpected")

    assert extract_requirements("", client=client) == []
    assert extract_requirements("SQL", client=client) == []
    assert client.calls == []


def test_rejects_invalid_or_malformed_model_response():
    with pytest.raises(RuntimeError, match="invalid JD analysis JSON"):
        extract_requirements("A sufficiently long job description.", client=FakeClient("{"))

    with pytest.raises(RuntimeError, match="contains invalid requirements"):
        extract_requirements(
            "A sufficiently long job description.",
            client=FakeClient(response([requirement("SQL", "maybe")])),
        )


def test_deduplicates_requirements_case_insensitively():
    client = FakeClient(response([
        requirement("SQL", "required"),
        requirement(" sql ", "required"),
        requirement("Python", "preferred"),
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [(item.requirement, item.evidence_level) for item in result] == [
        ("SQL", "required"),
        ("Python", "preferred"),
    ]


def test_requires_structured_requirement_list():
    client = FakeClient(json.dumps({"requirements": {"requirement": "SQL"}}))

    with pytest.raises(RuntimeError, match="requirements list"):
        extract_requirements("A sufficiently long job description.", client=client)


def test_splits_multi_tool_proficiency_requirement():
    client = FakeClient(response([
        requirement("Proficiency in Microsoft Excel and PowerPoint", "required")
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.requirement for item in result] == ["Microsoft Excel", "PowerPoint"]
    assert all(item.evidence_level == "required" for item in result)


def test_splits_multi_skill_sentence_and_preserves_meaning():
    client = FakeClient(response([
        requirement("Basic knowledge of SQL and Python for data analysis", "required")
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.requirement for item in result] == ["SQL", "Python", "data analysis"]


def test_reduces_responsibility_sentences_to_atomic_phrases():
    client = FakeClient(response([
        requirement("Generating and submitting required metrics and reports", "required"),
        requirement(
            "Investigating programming or process-related issues, identifying root causes, and providing resolutions",
            "implicit",
        ),
        requirement("Experience creating dashboards, KPIs, and automated reports", "preferred"),
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.requirement for item in result] == [
        "Metrics reporting",
        "Issue investigation",
        "Root cause analysis",
        "Problem resolution",
        "Dashboard development",
        "KPI reporting",
        "Automated reporting",
    ]
    assert result[1].evidence_level == "implicit"
    assert result[4].evidence_level == "preferred"


def test_deduplicates_near_duplicate_skill_phrases():
    client = FakeClient(response([
        requirement("SQL", "required"),
        requirement("Knowledge of SQL", "required"),
        requirement("SQL querying", "required"),
        requirement("Power BI", "preferred"),
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.requirement for item in result] == ["SQL", "Power BI"]


def test_atomicization_keeps_original_supporting_evidence():
    client = FakeClient(response([
        requirement("Proficiency in Excel and PowerPoint", "preferred", ["JD sentence"])
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.supporting_evidence for item in result] == [["JD sentence"], ["JD sentence"]]


def test_splits_including_clause_and_partial_issue_phrases():
    client = FakeClient(response([
        requirement("Informatica-related tools, including Panther", "required"),
        requirement("Identifying root causes and providing resolutions", "implicit"),
    ]))

    result = extract_requirements("A sufficiently long job description.", client=client)

    assert [item.requirement for item in result] == [
        "Informatica-related tools",
        "Panther",
        "Root cause analysis",
        "Problem resolution",
    ]

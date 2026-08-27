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

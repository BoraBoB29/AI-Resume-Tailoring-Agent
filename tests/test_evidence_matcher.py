from src.evidence_matcher import (
    EvidenceMatch,
    match_evidence,
    find_evidence,
    supported_requirements,
)


def test_match_evidence_finds_supporting_bullets():
    requirements = [
        "Python",
        "SQL",
        "Product Management",
    ]

    evidence = [
        "Built Python automation workflows.",
        "Used SQL to analyze operational data.",
        "Led product management initiatives.",
    ]

    results = match_evidence(
        requirements,
        evidence,
    )

    assert len(results) == 3

    assert all(
        isinstance(result, EvidenceMatch)
        for result in results
    )

    assert all(
        result.supported
        for result in results
    )


def test_match_evidence_identifies_missing_evidence():
    requirements = [
        "Python",
        "AWS",
    ]

    evidence = [
        "Built Python automation workflows.",
    ]

    results = match_evidence(
        requirements,
        evidence,
    )

    assert len(results) == 2

    python_result = results[0]
    aws_result = results[1]

    assert python_result.supported is True
    assert python_result.evidence

    assert aws_result.supported is False
    assert aws_result.evidence == []


def test_match_evidence_matches_phrases():
    requirements = [
        "Product Management",
        "Stakeholder Management",
    ]

    evidence = [
        "Worked on product management initiatives.",
        "Managed communication with key stakeholders.",
    ]

    results = match_evidence(
        requirements,
        evidence,
    )

    assert results[0].supported is True
    assert results[1].supported is True


def test_match_evidence_empty_requirements():
    results = match_evidence(
        [],
        ["Python experience"],
    )

    assert results == []


def test_match_evidence_empty_evidence():
    results = match_evidence(
        ["Python", "SQL"],
        [],
    )

    assert len(results) == 2
    assert all(
        result.supported is False
        for result in results
    )


def test_find_evidence():
    evidence = [
        "Developed Python automation tools.",
        "Created SQL reporting workflows.",
        "Managed project delivery.",
    ]

    result = find_evidence(
        "Python",
        evidence,
    )

    assert len(result) == 1
    assert "Python" in result[0]


def test_find_evidence_returns_empty_when_missing():
    evidence = [
        "Developed Python automation tools.",
    ]

    result = find_evidence(
        "AWS",
        evidence,
    )

    assert result == []


def test_supported_requirements():
    requirements = [
        "Python",
        "SQL",
        "AWS",
    ]

    evidence = [
        "Built Python automation.",
        "Used SQL for reporting.",
    ]

    result = supported_requirements(
        requirements,
        evidence,
    )

    assert "Python" in result
    assert "SQL" in result
    assert "AWS" not in result
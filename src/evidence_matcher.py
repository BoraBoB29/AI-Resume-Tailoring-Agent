from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class EvidenceMatch:
    requirement: str
    matched: bool
    evidence: list[str]

    @property
    def supported(self) -> bool:
        return self.matched


def _normalize(text):
    """Normalize either a requirement object or plain text."""
    if hasattr(text, "requirement"):
        text = text.requirement

    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    return " ".join(text.split())


def _words(text: str) -> set[str]:
    return set(_normalize(text).split())


def _stem(word: str) -> str:
    """
    Very small normalization layer for common word variants.

    Examples:
        managed -> manage
        management -> manage
        stakeholders -> stakeholder
    """

    word = word.lower()

    suffixes = (
        "ments",
        "ment",
        "ing",
        "ed",
        "ies",
        "es",
        "s",
    )

    for suffix in suffixes:
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            word = word[:-len(suffix)]
            break

    if word.endswith("i"):
        word = word[:-1] + "y"

    return word


def _concept_words(text: str) -> set[str]:
    return {_stem(word) for word in _words(text)}


def _requirement_supported(requirement, evidence):
    """Check whether evidence supports a JD requirement."""
    
    if hasattr(requirement, "requirement"):
        requirement = requirement.requirement

    if hasattr(evidence, "text"):
        evidence = evidence.text

    requirement_words = _concept_words(requirement)
    evidence_words = _concept_words(evidence)

    return bool(requirement_words & evidence_words)

    return len(matched_words) >= len(requirement_words) / 2


def match_evidence(
    requirements: list[str],
    evidence: list[str],
) -> list[EvidenceMatch]:

    results: list[EvidenceMatch] = []

    for requirement in requirements:
        matched_evidence = [
            item
            for item in evidence
            if _requirement_supported(requirement, item)
        ]

        results.append(
            EvidenceMatch(
                requirement=requirement,
                matched=bool(matched_evidence),
                evidence=matched_evidence,
            )
        )

    return results


def find_evidence(
    requirement: str,
    evidence: list[str],
) -> list[str]:
    """Return evidence statements supporting a requirement."""

    return [
        item
        for item in evidence
        if _requirement_supported(requirement, item)
    ]


def supported_requirements(
    requirements: list[str],
    evidence: list[str],
) -> list[str]:
    """Return requirements supported by the supplied evidence."""

    return [
        result.requirement
        for result in match_evidence(requirements, evidence)
        if result.supported
    ]


def match_requirements(
    requirements,
    resume_text: str,
) -> list[EvidenceMatch]:
    """
    Match JD requirements against resume text.

    Accepts requirements as strings or requirement objects
    containing a `text` attribute.
    """

    evidence = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", resume_text)
        if sentence.strip()
    ]

    normalized_requirements = []

    for requirement in requirements:
        if isinstance(requirement, str):
            normalized_requirements.append(requirement)
        elif hasattr(requirement, "text"):
            normalized_requirements.append(requirement.text)
        else:
            normalized_requirements.append(str(requirement))

    return match_evidence(
        normalized_requirements,
        evidence,
    )
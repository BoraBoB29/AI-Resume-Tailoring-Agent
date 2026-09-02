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


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


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


def _requirement_supported(
    requirement: str,
    evidence: str,
) -> bool:

    requirement_words = _concept_words(requirement)
    evidence_words = _concept_words(evidence)

    if not requirement_words:
        return False

    # Exact phrase match.
    requirement_normalized = _normalize(requirement)
    evidence_normalized = _normalize(evidence)

    if requirement_normalized in evidence_normalized:
        return True

    # Concept-level matching.
    matched_words = requirement_words.intersection(evidence_words)

    # For multi-word requirements, allow the majority of concepts
    # to match. This handles:
    #
    # "Stakeholder Management"
    # vs
    # "Managed communication with key stakeholders."
    #
    # -> manage + stakeholder
    if len(requirement_words) == 1:
        return bool(matched_words)

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
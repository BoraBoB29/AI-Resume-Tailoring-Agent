"""Deterministically match structured JD requirements to resume evidence."""

import re
from typing import Iterable, List, Tuple

from src.schema import JDRequirement


_STOPWORDS = {
    "a", "an", "and", "be", "by", "for", "have", "in", "of", "on",
    "or", "the", "to", "with", "years", "year",
}

_SYNONYMS = {
    "bachelor": {"bachelor", "btech", "b.tech", "engineering", "undergraduate"},
    "degree": {"degree", "bachelor", "btech", "b.tech", "engineering"},
    "dashboard": {"dashboard", "dashboards"},
    "dashboards": {"dashboard", "dashboards"},
    "python": {"python"},
    "sql": {"sql"},
    "powerbi": {"powerbi", "power", "bi"},
    "power": {"powerbi", "power"},
    "bi": {"powerbi", "bi"},
}


def _normalize(text: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(text).casefold()).strip()


def _tokens(text: object) -> set[str]:
    return {
        token
        for token in _normalize(text).split()
        if token not in _STOPWORDS
    }


def _matches(requirement: str, evidence: str) -> bool:
    requirement_text = _normalize(requirement)
    evidence_text = _normalize(evidence)

    if not requirement_text or not evidence_text:
        return False

    if requirement_text in evidence_text:
        return True

    requirement_tokens = _tokens(requirement_text)
    evidence_tokens = _tokens(evidence_text)
    if not requirement_tokens:
        return False

    for token in requirement_tokens:
        alternatives = _SYNONYMS.get(token, {token})
        if not alternatives.intersection(evidence_tokens):
            return False

    return True


def _source_entries(master_resume: dict) -> Iterable[Tuple[str, str]]:
    skills = master_resume.get("skills", {})
    if isinstance(skills, dict):
        categories = skills.get("categories", skills)
        if isinstance(categories, dict):
            for category, values in categories.items():
                if isinstance(values, list):
                    for index, value in enumerate(values):
                        yield f"skills.{category}[{index}]", str(value)

    experience = master_resume.get("experience", [])
    if isinstance(experience, list):
        for experience_item in experience:
            if not isinstance(experience_item, dict):
                continue
            company = str(experience_item.get("company", "")).strip()
            if not company:
                continue
            bullets = experience_item.get("bullets", [])
            if isinstance(bullets, list):
                for index, bullet in enumerate(bullets):
                    yield f"experience.{company}.bullets[{index}]", str(bullet)

    projects = master_resume.get("projects", [])
    if isinstance(projects, list):
        for project in projects:
            if not isinstance(project, dict):
                continue
            name = str(project.get("name", "")).strip()
            if not name:
                continue
            tech_stack = project.get("tech_stack", [])
            if isinstance(tech_stack, list):
                for index, technology in enumerate(tech_stack):
                    yield f"projects.{name}.tech_stack[{index}]", str(technology)
            bullets = project.get("bullets", [])
            if isinstance(bullets, list):
                for index, bullet in enumerate(bullets):
                    yield f"projects.{name}.bullets[{index}]", str(bullet)

    certifications = master_resume.get("certifications", [])
    if isinstance(certifications, list):
        for index, certification in enumerate(certifications):
            if isinstance(certification, dict):
                value = " ".join(
                    str(certification.get(field, ""))
                    for field in ("name", "issuer", "category")
                )
            else:
                value = str(certification)
            yield f"certifications[{index}]", value

    education = master_resume.get("education", [])
    if isinstance(education, list):
        for index, education_item in enumerate(education):
            if not isinstance(education_item, dict):
                continue
            value = " ".join(
                str(education_item.get(field, ""))
                for field in ("institution", "degree", "details")
            )
            yield f"education[{index}]", value


def match_evidence(
    requirements: Iterable[JDRequirement],
    master_resume: dict,
) -> List[JDRequirement]:
    """Return requirement copies populated with real master-resume references."""
    if not isinstance(master_resume, dict):
        master_resume = {}

    entries = list(_source_entries(master_resume))
    matched = []

    for requirement in requirements or []:
        if not isinstance(requirement, JDRequirement):
            requirement = JDRequirement.model_validate(requirement)

        references = [
            reference
            for reference, value in entries
            if _matches(requirement.requirement, value)
        ]
        matched.append(
            requirement.model_copy(
                update={"supporting_evidence": list(dict.fromkeys(references))}
            )
        )

    return matched

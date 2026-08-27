"""Deterministic ATS keyword coverage scoring."""

import re
from typing import Iterable, List

from pydantic import BaseModel, Field

from src.schema import JDRequirement


class ATSScore(BaseModel):
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    coverage_pct: float = 0.0
    required_matched: int = 0
    required_missing: int = 0
    preferred_matched: int = 0
    preferred_missing: int = 0
    implicit_matched: List[str] = Field(default_factory=list)


def _resume_text(tailored_resume) -> str:
    """Build searchable text from resume fields, without JSON formatting."""
    if hasattr(tailored_resume, "model_dump"):
        tailored_resume = tailored_resume.model_dump()
    if not isinstance(tailored_resume, dict):
        return ""

    values = []
    values.append(tailored_resume.get("summary", ""))

    skills = tailored_resume.get("skills", {})
    if isinstance(skills, dict):
        categories = skills.get("categories", skills)
        if isinstance(categories, dict):
            for category, items in categories.items():
                values.append(category)
                if isinstance(items, list):
                    values.extend(items)

    for section_name in ("experience", "projects", "education"):
        section = tailored_resume.get(section_name, [])
        if not isinstance(section, list):
            continue
        for item in section:
            if not isinstance(item, dict):
                continue
            for field in ("name", "company", "title", "degree", "institution"):
                values.append(item.get(field, ""))
            for field in ("bullets", "details", "tech_stack"):
                field_values = item.get(field, [])
                if isinstance(field_values, list):
                    values.extend(field_values)
            values.append(item.get("description", ""))

    certifications = tailored_resume.get("certifications", [])
    if isinstance(certifications, list):
        for certification in certifications:
            if isinstance(certification, dict):
                values.extend(
                    certification.get(field, "")
                    for field in ("name", "issuer", "category")
                )
            else:
                values.append(certification)

    return " ".join(str(value) for value in values if value is not None)


def _normalize(text: object) -> str:
    normalized = re.sub(r"[^a-z0-9\s-]+", " ", str(text).casefold())
    return re.sub(r"\s+", " ", normalized).strip()


def _keyword_matches(requirement: str, resume_text: str) -> bool:
    requirement_normalized = _normalize(requirement)
    resume_normalized = _normalize(resume_text)
    if not requirement_normalized:
        return False
    if re.search(
        rf"(?<![a-z0-9-]){re.escape(requirement_normalized)}(?![a-z0-9-])",
        resume_normalized,
    ):
        return True

    aliases = {"power bi": "powerbi", "powerbi": "power bi"}
    alias = aliases.get(requirement_normalized)
    return bool(alias and re.search(
        rf"(?<![a-z0-9-]){re.escape(alias)}(?![a-z0-9-])",
        resume_normalized,
    ))


def score_keyword_coverage(
    tailored_resume,
    requirements: Iterable[JDRequirement],
) -> ATSScore:
    """Score required and preferred requirement coverage in a resume."""
    resume_text = _resume_text(tailored_resume)
    matched = []
    missing = []
    implicit_matched = []
    required_matched = required_missing = 0
    preferred_matched = preferred_missing = 0
    seen_requirements = set()

    for requirement in requirements or []:
        if not isinstance(requirement, JDRequirement):
            requirement = JDRequirement.model_validate(requirement)
        name = requirement.requirement.strip()
        if not name:
            continue
        requirement_key = (name.casefold(), requirement.evidence_level)
        if requirement_key in seen_requirements:
            continue
        seen_requirements.add(requirement_key)
        is_match = _keyword_matches(name, resume_text)

        if requirement.evidence_level == "implicit":
            if is_match:
                implicit_matched.append(name)
            continue

        if is_match:
            matched.append(name)
            if requirement.evidence_level == "required":
                required_matched += 1
            else:
                preferred_matched += 1
        else:
            missing.append(name)
            if requirement.evidence_level == "required":
                required_missing += 1
            else:
                preferred_missing += 1

    scored_total = required_matched + required_missing + preferred_matched + preferred_missing
    coverage_pct = (
        round((required_matched + preferred_matched) * 100 / scored_total, 2)
        if scored_total
        else 0.0
    )

    return ATSScore(
        matched_keywords=list(dict.fromkeys(matched)),
        missing_keywords=list(dict.fromkeys(missing)),
        coverage_pct=coverage_pct,
        required_matched=required_matched,
        required_missing=required_missing,
        preferred_matched=preferred_matched,
        preferred_missing=preferred_missing,
        implicit_matched=list(dict.fromkeys(implicit_matched)),
    )


def print_ats_score(score: ATSScore) -> None:
    """Print a concise ATS coverage report."""
    required_total = score.required_matched + score.required_missing
    preferred_total = score.preferred_matched + score.preferred_missing
    required_pct = (
        round(score.required_matched * 100 / required_total, 2)
        if required_total else 0.0
    )
    preferred_pct = (
        round(score.preferred_matched * 100 / preferred_total, 2)
        if preferred_total else 0.0
    )

    print("========== ATS SCORE ==========")
    print(f"Required coverage: {score.required_matched}/{required_total} ({required_pct}%)")
    print(f"Preferred coverage: {score.preferred_matched}/{preferred_total} ({preferred_pct}%)")
    print(f"Overall coverage: {score.coverage_pct}%")
    print("Matched:")
    for keyword in score.matched_keywords:
        print(f"- {keyword}")
    print("Missing:")
    for keyword in score.missing_keywords:
        print(f"- {keyword}")
    print("================================")

"""Deterministic checks for unsupported generated resume claims."""

import re
from typing import List

from pydantic import BaseModel, Field


class UnsupportedBullet(BaseModel):
    section: str
    source_name: str
    index: int
    bullet: str
    reasons: List[str] = Field(default_factory=list)


_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into",
    "of", "on", "or", "the", "their", "this", "to", "using", "with",
    "worked", "work", "supported", "helped", "provided", "created",
}

_KNOWN_TECHNOLOGY_TERMS = {
    "airflow", "aws", "azure", "confluence", "excel", "git", "informatica",
    "java", "jira", "matlab", "numpy", "pandas", "power bi", "powerbi",
    "python", "r", "sql", "tableau", "tensorflow", "workato", "yolov5",
}


def _normalize(text: object) -> str:
    return re.sub(r"[^a-z0-9%+.]+", " ", str(text).casefold()).strip()


def _tokens(text: object) -> set[str]:
    return {
        token for token in _normalize(text).split()
        if token not in _STOPWORDS and len(token) > 1
    }


def _flatten(value: object) -> str:
    if isinstance(value, list):
        return " ".join(_flatten(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_flatten(item) for item in value.values())
    return str(value or "")


def _canonical_experience(master_resume: dict, company: str) -> dict | None:
    for item in master_resume.get("experience", []):
        if isinstance(item, dict) and item.get("company", "").casefold() == company.casefold():
            return item
    return None


def _canonical_project(master_resume: dict, name: str) -> dict | None:
    for item in master_resume.get("projects", []):
        if isinstance(item, dict) and item.get("name", "").casefold() == name.casefold():
            return item
    return None


def _known_terms(master_resume: dict) -> set[str]:
    values = []
    skills = master_resume.get("skills", {})
    if isinstance(skills, dict):
        values.extend(_flatten(skills.get("categories", skills)).casefold().split("\n"))
    for item in master_resume.get("experience", []) + master_resume.get("projects", []):
        if isinstance(item, dict):
            values.extend(_flatten(item.get("tools", [])).casefold().split("\n"))
            values.extend(_flatten(item.get("tech_stack", [])).casefold().split("\n"))
    return {term.strip() for term in values if term.strip()}


def _unsupported_metrics(bullet: str, source_text: str) -> List[str]:
    reasons = []
    for metric in re.findall(r"\b\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*(?:k|m|million|thousand|hours?|days?|months?|years?)\b", bullet.casefold()):
        if _normalize(metric) not in _normalize(source_text):
            reasons.append(f'unsupported metric "{metric.strip()}"')
    return reasons


def _unsupported_technologies(bullet: str, master_resume: dict) -> List[str]:
    normalized_bullet = _normalize(bullet)
    known_source = _known_terms(master_resume)
    reasons = []
    for term in _KNOWN_TECHNOLOGY_TERMS:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", normalized_bullet):
            if not any(term in _normalize(source_term) or _normalize(source_term) in term for source_term in known_source):
                reasons.append(f'unsupported technology/tool "{term}"')
    return reasons


def _bullet_reason(bullet: str, source_text: str, master_resume: dict) -> List[str]:
    reasons = _unsupported_metrics(bullet, source_text)
    reasons.extend(_unsupported_technologies(bullet, master_resume))
    generated_tokens = _tokens(bullet)
    source_tokens = _tokens(source_text)
    overlap = generated_tokens & source_tokens
    if generated_tokens and (len(generated_tokens) < 3 or len(overlap) < 2 or len(overlap) / len(generated_tokens) < 0.25):
        reasons.append("claim is not adequately supported by canonical resume evidence")
    return list(dict.fromkeys(reasons))


def flag_unsupported_bullets(tailored_resume, master_resume: dict) -> List[UnsupportedBullet]:
    """Return generated experience/project bullets needing factual review."""
    if hasattr(tailored_resume, "model_dump"):
        tailored_resume = tailored_resume.model_dump()
    if not isinstance(tailored_resume, dict) or not isinstance(master_resume, dict):
        return []

    flags = []
    for section in ("experience", "projects"):
        items = tailored_resume.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            source_name = str(item.get("company" if section == "experience" else "name", "")).strip()
            canonical = (
                _canonical_experience(master_resume, source_name)
                if section == "experience"
                else _canonical_project(master_resume, source_name)
            )
            if not canonical:
                for index, bullet in enumerate(item.get("bullets", []) if isinstance(item.get("bullets", []), list) else []):
                    flags.append(UnsupportedBullet(
                        section=section, source_name=source_name, index=index,
                        bullet=str(bullet), reasons=[f"unknown {section[:-1]} '{source_name}'"],
                    ))
                continue

            source_text = _flatten(canonical)
            for field in (("bullets", "tools", "domain") if section == "experience" else ("bullets", "tech_stack")):
                source_text += " " + _flatten(canonical.get(field, []))
            bullets = item.get("bullets", [])
            if not isinstance(bullets, list):
                continue
            for index, bullet in enumerate(bullets):
                reasons = _bullet_reason(str(bullet), source_text, master_resume)
                if reasons:
                    flags.append(UnsupportedBullet(
                        section=section, source_name=source_name, index=index,
                        bullet=str(bullet), reasons=reasons,
                    ))

    return flags


def print_evidence_check(flags: List[UnsupportedBullet], total_bullets: int) -> None:
    """Print a concise report without changing generated resume content."""
    print("========== EVIDENCE CHECK ==========")
    print(f"Supported bullets: {max(total_bullets - len(flags), 0)}")
    print(f"Flagged bullets: {len(flags)}")
    if flags:
        print("Flagged:")
        for flag in flags:
            print(f"- [{flag.source_name}] {flag.bullet}")
            print(f"  Reason: {'; '.join(flag.reasons)}")
    print("====================================")

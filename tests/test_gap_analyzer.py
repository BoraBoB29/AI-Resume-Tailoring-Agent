from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillGap:
    requirement: str
    category: str = "SKILL"
    priority: str = "MEDIUM"

    @property
    def severity(self) -> str:
        """Backward-compatible alias for priority."""
        return self.priority


def analyze_gaps(
    ats_score,
    requirement_categories: dict[str, str] | None = None,
) -> list[SkillGap]:

    requirement_categories = requirement_categories or {}

    gaps: list[SkillGap] = []

    # Required gaps are HIGH priority
    for requirement in ats_score.missing_required:
        category = requirement_categories.get(
            requirement.lower(),
            "SKILL",
        )

        gaps.append(
            SkillGap(
                requirement=requirement,
                category=category,
                priority="HIGH",
            )
        )

    # Preferred gaps are MEDIUM priority
    for requirement in ats_score.missing_preferred:
        category = requirement_categories.get(
            requirement.lower(),
            "SKILL",
        )

        gaps.append(
            SkillGap(
                requirement=requirement,
                category=category,
                priority="MEDIUM",
            )
        )

    return gaps
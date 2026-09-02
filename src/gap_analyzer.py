from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SkillGap:
    """
    Represents a missing skill or requirement.

    priority:
        HIGH   -> required requirement
        MEDIUM -> preferred requirement
    """

    requirement: str
    category: str = "SKILL"
    priority: str = "MEDIUM"

    @property
    def severity(self) -> str:
        """
        Backward-compatible alias.

        Older code may refer to severity instead of priority.
        """

        return self.priority


def analyze_gaps(
    ats_score,
    requirement_categories: dict[str, str] | None = None,
) -> list[SkillGap]:
    """
    Identify missing requirements from an ATS score.
    """

    requirement_categories = (
        requirement_categories or {}
    )

    gaps: list[SkillGap] = []

    # ---------------------------------------------------------
    # Required requirements
    # ---------------------------------------------------------

    for requirement in getattr(
        ats_score,
        "missing_required",
        [],
    ):

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

    # ---------------------------------------------------------
    # Preferred requirements
    # ---------------------------------------------------------

    for requirement in getattr(
        ats_score,
        "missing_preferred",
        [],
    ):

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
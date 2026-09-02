from __future__ import annotations

from dataclasses import dataclass

from src.ats_scorer import ATSScore, calculate_ats_score
from src.evidence_matcher import (
    EvidenceMatch,
    match_requirements,
)
from src.gap_analyzer import SkillGap, analyze_gaps
from src.jd_analyzer import JDAnalysis, analyze_job_description


@dataclass
class JDIntelligenceResult:
    analysis: JDAnalysis
    required_matches: list[EvidenceMatch]
    preferred_matches: list[EvidenceMatch]
    ats_score: ATSScore
    gaps: list[SkillGap]


def analyze_candidate_against_job(
    job_description: str,
    resume_text: str,
) -> JDIntelligenceResult:

    analysis = analyze_job_description(
        job_description
    )

    required_matches = match_requirements(
        analysis.required,
        resume_text,
    )

    preferred_matches = match_requirements(
        analysis.preferred,
        resume_text,
    )

    ats_score = calculate_ats_score(
        required_matches=required_matches,
        preferred_matches=preferred_matches,
    )

    # JDAnalysis contains required and preferred requirements,
    # so combine them for gap-category lookup.
    all_requirements = (
        analysis.required +
        analysis.preferred
    )

    categories = {
        item.lower(): (
            "preferred"
            if item in analysis.preferred
            else "required"
        )
        for item in all_requirements
    }

    gaps = analyze_gaps(
        ats_score,
        requirement_categories=categories,
    )

    return JDIntelligenceResult(
        analysis=analysis,
        required_matches=required_matches,
        preferred_matches=preferred_matches,
        ats_score=ats_score,
        gaps=gaps,
    )
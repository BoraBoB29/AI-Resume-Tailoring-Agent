from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ATSScore:
    """
    Represents ATS keyword/evidence scoring.

    Score fields are percentages from 0 to 100.
    Coverage fields are normalized values from 0 to 1.
    """

    required_score: float = 100.0
    preferred_score: float = 100.0
    overall_score: float = 100.0

    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

    # Evidence-match compatibility fields
    matched_required: list = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)

    matched_preferred: list = field(default_factory=list)
    missing_preferred: list[str] = field(default_factory=list)

    # Legacy counters
    required_missing: int = 0
    preferred_missing: int = 0

    # Legacy keyword list
    missing_keywords: list[str] = field(default_factory=list)

    # Normalized coverage: 0.0 - 1.0
    required_coverage: float = 1.0
    preferred_coverage: float = 1.0
    overall_coverage: float = 1.0

    # Counters
    required_total: int = 0
    required_matched: int = 0
    preferred_total: int = 0
    preferred_matched: int = 0

    def __post_init__(self) -> None:
        """
        Keep compatibility fields synchronized.
        """

        # If coverage was explicitly left at its default,
        # derive it from the percentage score.
        if (
            self.required_coverage == 1.0
            and self.required_score != 100.0
        ):
            self.required_coverage = (
                self.required_score / 100.0
            )

        if (
            self.preferred_coverage == 1.0
            and self.preferred_score != 100.0
        ):
            self.preferred_coverage = (
                self.preferred_score / 100.0
            )

        if (
            self.overall_coverage == 1.0
            and self.overall_score != 100.0
        ):
            self.overall_coverage = (
                self.overall_score / 100.0
            )

        # Keep missing lists synchronized.
        if not self.missing_required and self.missing:
            self.missing_required = list(self.missing)

        if not self.missing and self.missing_required:
            self.missing = list(self.missing_required)

        # Keep preferred missing list synchronized.
        if (
            not self.missing_preferred
            and self.preferred_missing
        ):
            self.missing_preferred = list(
                self.missing_preferred
            )

        # Keep legacy counters synchronized.
        if self.required_missing == 0:
            self.required_missing = len(
                self.missing_required
            )

        if self.preferred_missing == 0:
            self.preferred_missing = len(
                self.missing_preferred
            )

        # Keep matched counters sensible.
        if self.required_matched == 0 and self.required_total == 0:
            self.required_matched = len(
                self.matched_required
            )

        if self.preferred_matched == 0 and self.preferred_total == 0:
            self.preferred_matched = len(
                self.matched_preferred
            )

        # Legacy missing keyword list.
        if not self.missing_keywords and self.missing:
            self.missing_keywords = list(self.missing)


def _coverage(
    keywords: list[str],
    resume_text: str,
) -> tuple[float, list[str], list[str]]:
    """
    Calculate keyword coverage.

    Matching is case-insensitive substring matching.
    Returns:
        score,
        matched keywords,
        missing keywords
    """

    if not isinstance(resume_text, str):
        raise TypeError(
            "resume_text must be a string."
        )

    resume_lower = resume_text.lower()

    if not keywords:
        return 100.0, [], []

    matched: list[str] = []
    missing: list[str] = []

    for keyword in keywords:
        keyword = str(keyword).strip()

        if not keyword:
            continue

        if keyword.lower() in resume_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)

    total = len(matched) + len(missing)

    if total == 0:
        return 100.0, matched, missing

    score = (
        len(matched) / total
    ) * 100.0

    return score, matched, missing


def score_keyword_coverage(
    resume_text: str,
    required_keywords: list[str] | None = None,
    preferred_keywords: list[str] | None = None,
) -> ATSScore:
    """
    Score resume coverage against required and preferred keywords.
    """

    if not isinstance(resume_text, str):
        raise TypeError(
            "resume_text must be a string."
        )

    required_keywords = (
        required_keywords or []
    )

    preferred_keywords = (
        preferred_keywords or []
    )

    (
        required_score,
        required_matched,
        missing_required,
    ) = _coverage(
        required_keywords,
        resume_text,
    )

    (
        preferred_score,
        preferred_matched,
        missing_preferred,
    ) = _coverage(
        preferred_keywords,
        resume_text,
    )

    if required_keywords and preferred_keywords:
        overall_score = (
            required_score +
            preferred_score
        ) / 2.0

    elif required_keywords:
        overall_score = required_score

    elif preferred_keywords:
        overall_score = preferred_score

    else:
        overall_score = 100.0

    matched = (
        required_matched +
        preferred_matched
    )

    missing = (
        missing_required +
        missing_preferred
    )

    return ATSScore(
        required_score=required_score,
        preferred_score=preferred_score,
        overall_score=overall_score,

        matched=matched,
        missing=missing,

        matched_required=required_matched,
        missing_required=missing_required,

        matched_preferred=preferred_matched,
        missing_preferred=missing_preferred,

        required_missing=len(
            missing_required
        ),
        preferred_missing=len(
            missing_preferred
        ),

        missing_keywords=missing,

        required_coverage=(
            required_score / 100.0
        ),
        preferred_coverage=(
            preferred_score / 100.0
        ),
        overall_coverage=(
            overall_score / 100.0
        ),

        required_total=len(
            required_keywords
        ),
        required_matched=len(
            required_matched
        ),

        preferred_total=len(
            preferred_keywords
        ),
        preferred_matched=len(
            preferred_matched
        ),
    )


def calculate_ats_score(
    required_matches=None,
    preferred_matches=None,
) -> ATSScore:
    """
    Calculate ATS score from EvidenceMatch objects.

    Supports both:
        .supported
    and:
        .matched
    """

    required_matches = (
        required_matches or []
    )

    preferred_matches = (
        preferred_matches or []
    )

    def is_supported(match) -> bool:
        if hasattr(match, "supported"):
            return bool(match.supported)

        if hasattr(match, "matched"):
            return bool(match.matched)

        return False

    # -----------------------------
    # Required requirements
    # -----------------------------

    required_matched_objects = [
        match
        for match in required_matches
        if is_supported(match)
    ]

    required_missing = [
        getattr(
            match,
            "requirement",
            str(match),
        )
        for match in required_matches
        if not is_supported(match)
    ]

    # -----------------------------
    # Preferred requirements
    # -----------------------------

    preferred_matched_objects = [
        match
        for match in preferred_matches
        if is_supported(match)
    ]

    preferred_missing = [
        getattr(
            match,
            "requirement",
            str(match),
        )
        for match in preferred_matches
        if not is_supported(match)
    ]

    # -----------------------------
    # Counts
    # -----------------------------

    required_total = len(
        required_matches
    )

    preferred_total = len(
        preferred_matches
    )

    required_matched_count = len(
        required_matched_objects
    )

    preferred_matched_count = len(
        preferred_matched_objects
    )

    # -----------------------------
    # Scores
    # -----------------------------

    if required_total:
        required_score = (
            required_matched_count /
            required_total
        ) * 100.0
    else:
        required_score = 100.0

    if preferred_total:
        preferred_score = (
            preferred_matched_count /
            preferred_total
        ) * 100.0
    else:
        preferred_score = 100.0

    if required_total and preferred_total:
        overall_score = (
            required_score +
            preferred_score
        ) / 2.0

    elif required_total:
        overall_score = required_score

    elif preferred_total:
        overall_score = preferred_score

    else:
        overall_score = 100.0

    # -----------------------------
    # Human-readable matched values
    # -----------------------------

    matched = [
        getattr(
            match,
            "requirement",
            str(match),
        )
        for match in (
            required_matched_objects +
            preferred_matched_objects
        )
    ]

    missing = (
        required_missing +
        preferred_missing
    )

    # -----------------------------
    # Return
    # -----------------------------

    return ATSScore(
        required_score=required_score,
        preferred_score=preferred_score,
        overall_score=overall_score,

        matched=matched,
        missing=missing,

        matched_required=[
            getattr(
                match,
                "requirement",
                str(match),
            )
            for match in required_matched_objects
        ],

        missing_required=required_missing,

        matched_preferred=[
            getattr(
                match,
                "requirement",
                str(match),
            )
            for match in preferred_matched_objects
        ],

        missing_preferred=preferred_missing,

        required_missing=len(
            required_missing
        ),

        preferred_missing=len(
            preferred_missing
        ),

        missing_keywords=missing,

        required_coverage=(
            required_score / 100.0
        ),

        preferred_coverage=(
            preferred_score / 100.0
        ),

        overall_coverage=(
            overall_score / 100.0
        ),

        required_total=required_total,

        required_matched=(
            required_matched_count
        ),

        preferred_total=preferred_total,

        preferred_matched=(
            preferred_matched_count
        ),
    )


def score_resume(
    resume_text: str,
    required_keywords: list[str] | None = None,
    preferred_keywords: list[str] | None = None,
) -> ATSScore:
    """
    Compatibility alias for score_keyword_coverage.
    """

    return score_keyword_coverage(
        resume_text=resume_text,
        required_keywords=required_keywords,
        preferred_keywords=preferred_keywords,
    )


def print_ats_score(
    score: ATSScore,
) -> None:
    """
    Print ATS score in a human-readable format.
    """

    if not isinstance(score, ATSScore):
        raise TypeError(
            "score must be an ATSScore."
        )

    print("ATS SCORE")
    print("=========")

    print(
        f"Required Score: "
        f"{score.required_score:.2f}%"
    )

    print(
        f"Preferred Score: "
        f"{score.preferred_score:.2f}%"
    )

    print(
        f"Overall Score: "
        f"{score.overall_score:.2f}%"
    )

    print("Matched:")

    if score.matched:
        for item in score.matched:
            print(f"  - {item}")
    else:
        print("  - None")

    print("Missing:")

    if score.missing:
        for item in score.missing:
            print(f"  - {item}")
    else:
        print("  - None")
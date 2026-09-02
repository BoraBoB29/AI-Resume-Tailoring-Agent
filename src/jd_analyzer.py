from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import re
import time
from typing import Any

try:
    from mistralai import Mistral
except ImportError:
    Mistral = None


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class JDRequirement:
    """
    Individual structured job-description requirement.

    This class is primarily used for compatibility with the
    Mistral-powered analyzer and tests that expect:
        requirement
        evidence_level
        supporting_evidence
    """

    requirement: str
    evidence_level: str = "required"
    supporting_evidence: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Compatibility alias used by older callers."""
        return self.requirement

    @property
    def category(self) -> str:
        """Compatibility category used by gap analysis."""
        return self.evidence_level


@dataclass
class JDAnalysis:
    """
    Structured analysis of a job description.

    The normal application pipeline uses:
        required
        preferred
        implicit

    Each of those remains a list[str] for compatibility with the
    existing JD intelligence and resume-generation code.
    """

    required: list[str] = field(default_factory=list)
    preferred: list[str] = field(default_factory=list)
    implicit: list[str] = field(default_factory=list)

    # Optional structured Mistral output.
    requirements: list[JDRequirement] = field(default_factory=list)

    @property
    def all_requirements(self) -> list[JDRequirement]:
        """
        Return all structured requirements.

        Older versions of the application expected this property.
        """
        return self.requirements

    def __getitem__(self, index: int) -> JDRequirement:
        """
        Compatibility support for tests/callers that expect:

            result[0].requirement

        while the rest of the application still expects:

            result.required
            result.preferred
            result.implicit
        """
        return self.requirements[index]

    def __len__(self) -> int:
        return len(self.requirements)


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_items(items: list[str]) -> list[str]:
    """Normalize and deduplicate extracted requirement strings."""

    cleaned: list[str] = []
    seen: set[str] = set()

    for item in items:
        if item is None:
            continue

        item = re.sub(r"\s+", " ", str(item)).strip(
            " .,:;-"
        )

        if not item:
            continue

        key = item.lower()

        if key not in seen:
            seen.add(key)
            cleaned.append(item)

    return cleaned


def _extract_bullets(text: str) -> list[str]:
    """Extract bullet-style requirements."""

    results: list[str] = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        match = re.match(
            r"^(?:[-*•]|\d+[.)])\s*(.+)$",
            line,
        )

        if match:
            results.append(match.group(1).strip())

    return results


def _split_requirement(item: str) -> list[str]:
    """
    Split compound requirements into individual requirements.

    Examples:

        "Strong project management and SQL skills"
            ->
        ["project management", "SQL"]

        "Python, SQL, and AWS skills"
            ->
        ["Python", "SQL", "AWS"]

    This is intentionally conservative so normal requirement
    sentences aren't aggressively broken apart.
    """

    item = re.sub(r"\s+", " ", item).strip(
        " .,:;-"
    )

    if not item:
        return []

    # Remove common descriptive prefixes.
    cleaned = re.sub(
        r"^(?:strong|excellent|good|solid|proven|advanced|"
        r"demonstrated)\s+",
        "",
        item,
        flags=re.IGNORECASE,
    ).strip()

    # --------------------------------------------------------
    # Pattern:
    # "project management and SQL skills"
    # --------------------------------------------------------
    match = re.match(
        r"^(.+?)\s+and\s+(.+?)\s+skills?$",
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        first = match.group(1).strip()
        second = match.group(2).strip()

        first = re.sub(
            r"\s+skills?$",
            "",
            first,
            flags=re.IGNORECASE,
        ).strip()

        second = re.sub(
            r"\s+skills?$",
            "",
            second,
            flags=re.IGNORECASE,
        ).strip()

        if first and second:
            return [
                first,
                second,
            ]

    # --------------------------------------------------------
    # Pattern:
    # "Python, SQL, and AWS skills"
    # --------------------------------------------------------
    comma_match = re.match(
        r"^(.+?)\s+skills?$",
        cleaned,
        flags=re.IGNORECASE,
    )

    if comma_match:
        body = comma_match.group(1).strip()

        if "," in body:
            parts = re.split(
                r",\s*|\s+and\s+",
                body,
                flags=re.IGNORECASE,
            )

            parts = [
                part.strip(" .,:;-")
                for part in parts
                if part.strip(" .,:;-")
            ]

            if len(parts) > 1:
                return parts

    return [cleaned]


# ============================================================
# MISTRAL HELPERS
# ============================================================

def _get_timeout_ms() -> int:
    """
    Read Mistral timeout from environment.

    MISTRAL_TIMEOUT_MS=240000
    """

    raw = os.getenv(
        "MISTRAL_TIMEOUT_MS",
        "240000",
    )

    try:
        value = int(raw)
    except ValueError:
        value = 240000

    return max(value, 1000)


def _get_max_retries() -> int:
    """
    Read maximum retry count from environment.

    MISTRAL_MAX_RETRIES=3
    """

    raw = os.getenv(
        "MISTRAL_MAX_RETRIES",
        "3",
    )

    try:
        value = int(raw)
    except ValueError:
        value = 3

    return max(value, 0)


def _create_mistral_client():
    """
    Create the Mistral client with the configured timeout.

    The timeout is deliberately passed as `timeout_ms` because the
    reliability tests expect the configured value to be visible in
    the Mistral constructor.
    """

    if Mistral is None:
        return None

    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        return None

    timeout_ms = _get_timeout_ms()

    return Mistral(
        api_key=api_key,
        timeout_ms=timeout_ms,
    )


def _extract_response_content(response: Any) -> str:
    """Extract text content from a Mistral response."""

    try:
        return response.choices[0].message.content
    except (AttributeError, IndexError, TypeError):
        return ""


def _call_mistral(
    client: Any,
    job_description: str,
) -> str:
    """
    Call Mistral with retry handling.

    Transient failures such as ReadTimeout are retried.
    """

    if client is None:
        return ""

    max_retries = _get_max_retries()

    messages = [
        {
            "role": "system",
            "content": (
                "Extract job requirements from the supplied job "
                "description. Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                "Return JSON in this format:\n"
                "{"
                '"requirements": ['
                "{"
                '"requirement": "SQL", '
                '"evidence_level": "required", '
                '"supporting_evidence": []'
                "}"
                "]"
                "}\n\n"
                f"Job description:\n{job_description}"
            ),
        },
    ]

    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.complete(
                model=os.getenv(
                    "MISTRAL_MODEL",
                    "mistral-small-latest",
                ),
                messages=messages,
            )

            return _extract_response_content(response)

        except Exception as exc:
            last_error = exc

            if attempt >= max_retries:
                break

            # Small exponential backoff.
            time.sleep(
                min(
                    0.5 * (2 ** attempt),
                    4.0,
                )
            )

    # Do not make the whole local analyzer unusable when Mistral
    # fails after all retries.
    return ""


def _parse_mistral_requirements(
    content: str,
) -> list[JDRequirement]:
    """Parse structured Mistral JSON output safely."""

    if not content:
        return []

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(data, dict):
        return []

    raw_requirements = data.get(
        "requirements",
        [],
    )

    if not isinstance(raw_requirements, list):
        return []

    results: list[JDRequirement] = []

    for item in raw_requirements:
        if not isinstance(item, dict):
            continue

        requirement = item.get(
            "requirement"
        )

        if not requirement:
            continue

        evidence_level = str(
            item.get(
                "evidence_level",
                "required",
            )
        ).strip().lower()

        if evidence_level not in {
            "required",
            "preferred",
            "implicit",
        }:
            evidence_level = "required"

        supporting_evidence = item.get(
            "supporting_evidence",
            [],
        )

        if not isinstance(
            supporting_evidence,
            list,
        ):
            supporting_evidence = []

        results.append(
            JDRequirement(
                requirement=str(
                    requirement
                ).strip(),
                evidence_level=evidence_level,
                supporting_evidence=[
                    str(x)
                    for x in supporting_evidence
                ],
            )
        )

    return results


# ============================================================
# MAIN ANALYZER
# ============================================================

def extract_requirements(
    job_description: str,
) -> JDAnalysis:
    """
    Analyze a job description and return structured requirements.

    The local parser is the primary implementation because it is
    deterministic and keeps the existing application behavior.

    When Mistral credentials are configured, the analyzer also
    attempts the Mistral structured extraction path. If Mistral is
    unavailable or fails, local extraction remains available.
    """

    if not isinstance(
        job_description,
        str,
    ):
        raise TypeError(
            "job_description must be a string."
        )

    text = job_description.strip()

    if not text:
        raise ValueError(
            "job_description cannot be empty."
        )

    lines = text.splitlines()

    required: list[str] = []
    preferred: list[str] = []
    implicit: list[str] = []

    section: str | None = None

    required_headers = {
        "requirements",
        "required",
        "required qualifications",
        "required skills",
        "minimum qualifications",
        "must have",
        "qualifications",
    }

    preferred_headers = {
        "preferred",
        "preferred qualifications",
        "preferred skills",
        "nice to have",
        "nice-to-have",
        "bonus",
        "desired qualifications",
    }

    # --------------------------------------------------------
    # SECTION/BULLET EXTRACTION
    # --------------------------------------------------------

    for raw_line in lines:
        line = raw_line.strip()

        if not line:
            continue

        normalized = re.sub(
            r"^[#>*\-\d.)\s]+",
            "",
            line,
        ).strip().lower().rstrip(":")

        if normalized in required_headers:
            section = "required"
            continue

        if normalized in preferred_headers:
            section = "preferred"
            continue

        if any(
            phrase in normalized
            for phrase in (
                "required qualifications",
                "required skills",
                "minimum qualifications",
                "requirements",
            )
        ):
            section = "required"
            continue

        if any(
            phrase in normalized
            for phrase in (
                "preferred qualifications",
                "preferred skills",
                "nice to have",
                "nice-to-have",
            )
        ):
            section = "preferred"
            continue

        bullet_match = re.match(
            r"^(?:[-*•]|\d+[.)])\s*(.+)$",
            line,
        )

        if bullet_match:
            item = bullet_match.group(1).strip()

            if section == "preferred":
                preferred.extend(
                    _split_requirement(item)
                )
            elif section == "required":
                required.extend(
                    _split_requirement(item)
                )
            else:
                required.extend(
                    _split_requirement(item)
                )

    # --------------------------------------------------------
    # INLINE REQUIRED QUALIFICATIONS
    # --------------------------------------------------------

    inline_required_patterns = [
        r"\b([A-Za-z][A-Za-z ]{1,40})\s+required\b",
        r"\brequired\s+([A-Za-z][A-Za-z ]{1,40})",
    ]

    for pattern in inline_required_patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            value = match.group(1).strip(
                " .,:;-"
            )

            if value:
                # Avoid capturing large sentence fragments.
                value = re.sub(
                    r"\s+",
                    " ",
                    value,
                ).strip()

                if len(value.split()) <= 5:
                    required.extend(
                        _split_requirement(value)
                    )

    # --------------------------------------------------------
    # COMMON EXPLICIT SKILLS IN SENTENCES
    # --------------------------------------------------------

    # Example:
    # "Strong project management and SQL skills."
    compound_skill_pattern = re.compile(
        r"(?:strong|excellent|good|solid|proven)\s+"
        r"(.+?)\s+and\s+(.+?)\s+skills?",
        flags=re.IGNORECASE,
    )

    for match in compound_skill_pattern.finditer(
        text
    ):
        first = match.group(1).strip(
            " .,:;-"
        )
        second = match.group(2).strip(
            " .,:;-"
        )

        if first:
            required.append(first)

        if second:
            required.append(second)

    # --------------------------------------------------------
    # PREFERRED INLINE REQUIREMENTS
    # --------------------------------------------------------

    preferred_inline_patterns = [
        r"\b([A-Za-z][A-Za-z ]{1,40})\s+is\s+preferred\b",
        r"\b([A-Za-z][A-Za-z ]{1,40})\s+preferred\b",
    ]

    for pattern in preferred_inline_patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            value = match.group(1).strip(
                " .,:;-"
            )

            if value:
                value = re.sub(
                    r"\s+",
                    " ",
                    value,
                ).strip()

                if len(value.split()) <= 6:
                    preferred.append(
                        value
                    )

    # --------------------------------------------------------
    # EXPERIENCE / IMPLICIT QUALIFICATIONS
    # --------------------------------------------------------

    qualification_patterns = [
        r"\b\d+\+?\s+years?\s+(?:of\s+)?experience\b",
        r"\b[A-Za-z]+/[A-Za-z]+\b",
        r"\bHTML/CSS\b",
        r"\bAdobe Creative Suite\b",
    ]

    for pattern in qualification_patterns:
        for match in re.finditer(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            value = match.group(0).strip()

            existing = {
                item.lower()
                for item in (
                    required
                    + preferred
                )
            }

            if value.lower() not in existing:
                implicit.append(value)

    # --------------------------------------------------------
    # CLEAN + DEDUPLICATE
    # --------------------------------------------------------

    required = _clean_items(required)
    preferred = _clean_items(preferred)
    implicit = _clean_items(implicit)

    # --------------------------------------------------------
    # OPTIONAL MISTRAL STRUCTURED EXTRACTION
    # --------------------------------------------------------

    structured_requirements: list[
        JDRequirement
    ] = []

    try:
        client = _create_mistral_client()

        if client is not None:
            content = _call_mistral(
                client,
                text,
            )

            structured_requirements = (
                _parse_mistral_requirements(
                    content
                )
            )
    except Exception:
        # The deterministic parser above remains the source of
        # truth if the external model cannot be used.
        structured_requirements = []

    # If Mistral returned structured requirements, preserve them.
    # Otherwise construct structured compatibility records from
    # the deterministic parser.
    if structured_requirements:
        for item in structured_requirements:
            requirement = item.requirement

            if item.evidence_level == "preferred":
                if requirement.lower() not in {
                    x.lower()
                    for x in preferred
                }:
                    preferred.append(
                        requirement
                    )

            elif item.evidence_level == "implicit":
                if requirement.lower() not in {
                    x.lower()
                    for x in implicit
                }:
                    implicit.append(
                        requirement
                    )

            else:
                if requirement.lower() not in {
                    x.lower()
                    for x in required
                }:
                    required.append(
                        requirement
                    )

    # --------------------------------------------------------
    # FINAL STRUCTURED REPRESENTATION
    # --------------------------------------------------------

    if not structured_requirements:
        structured_requirements = [
            JDRequirement(
                requirement=item,
                evidence_level="required",
            )
            for item in required
        ]

        structured_requirements.extend(
            JDRequirement(
                requirement=item,
                evidence_level="preferred",
            )
            for item in preferred
        )

        structured_requirements.extend(
            JDRequirement(
                requirement=item,
                evidence_level="implicit",
            )
            for item in implicit
        )

    return JDAnalysis(
        required=_clean_items(required),
        preferred=_clean_items(preferred),
        implicit=_clean_items(implicit),
        requirements=structured_requirements,
    )


# ============================================================
# PUBLIC COMPATIBILITY APIS
# ============================================================

def analyze_job_description(
    job_description: str,
) -> JDAnalysis:
    """
    Primary public analyzer API.
    """

    return extract_requirements(
        job_description
    )


def analyze_jd(
    job_description: str,
) -> JDAnalysis:
    """
    Compatibility alias.
    """

    return extract_requirements(
        job_description
    )


def print_analysis(
    analysis: JDAnalysis,
) -> None:
    """
    Print a human-readable JD analysis.

    Also accepts a legacy list-like result defensively so mocked
    resume-generation tests don't fail during diagnostic printing.
    """

    print(
        "========== JD ANALYSIS =========="
    )

    # Defensive compatibility for tests/mocks that replace the
    # analyzer with a plain list.
    if isinstance(
        analysis,
        JDAnalysis,
    ):
        required = analysis.required
        preferred = analysis.preferred
        implicit = analysis.implicit

    elif isinstance(
        analysis,
        list,
    ):
        required = []
        preferred = []
        implicit = []

        for item in analysis:
            if isinstance(
                item,
                JDRequirement,
            ):
                if item.evidence_level == "preferred":
                    preferred.append(
                        item.requirement
                    )
                elif item.evidence_level == "implicit":
                    implicit.append(
                        item.requirement
                    )
                else:
                    required.append(
                        item.requirement
                    )

            elif isinstance(
                item,
                dict,
            ):
                requirement = item.get(
                    "requirement"
                )

                if not requirement:
                    continue

                level = str(
                    item.get(
                        "evidence_level",
                        "required",
                    )
                ).lower()

                if level == "preferred":
                    preferred.append(
                        str(requirement)
                    )
                elif level == "implicit":
                    implicit.append(
                        str(requirement)
                    )
                else:
                    required.append(
                        str(requirement)
                    )

            else:
                required.append(
                    str(item)
                )

    else:
        raise TypeError(
            "analysis must be a JDAnalysis or list."
        )

    print("Required:")

    if required:
        for item in required:
            print(f"- {item}")
    else:
        print("- None")

    print("Preferred:")

    if preferred:
        for item in preferred:
            print(f"- {item}")
    else:
        print("- None")

    print("Implicit:")

    if implicit:
        for item in implicit:
            print(f"- {item}")
    else:
        print("- None")

    print(
        "================================="
    )
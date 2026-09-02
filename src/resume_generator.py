from __future__ import annotations

from pathlib import Path
from datetime import datetime
import json
import re

import yaml

from src import config
from src.ats_scorer import print_ats_score, score_keyword_coverage
from src.evidence_matcher import match_evidence
from src.llm_tailor import tailor_resume
from src.latex_renderer import render_latex
from src.pdf_compiler import compile_pdf, get_pdf_page_count
from src.unsupported_claims import flag_unsupported_bullets, print_evidence_check
from src.jd_analyzer import (
    JDAnalysis,
    extract_requirements,
    print_analysis,
)


# ============================================================
# SLUGIFY
# ============================================================

def _slugify(text: str) -> str:
    text = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        text.strip(),
    ).strip("_")

    return text.lower() or "role"


# ============================================================
# REQUIREMENT HELPERS
# ============================================================

def _requirement_text(item) -> str:
    """
    Safely extract the plain-text requirement from any of the
    requirement representations used by the pipeline.

    Supported forms include:
      - plain strings
      - JDRequirement objects
      - EvidenceMatch objects containing JDRequirement
      - dictionaries
      - Pydantic models
      - generic objects
    """

    if item is None:
        return ""

    # Plain string
    if isinstance(item, str):
        return item.strip()

    # EvidenceMatch-like object:
    # EvidenceMatch.requirement may itself be a JDRequirement.
    if hasattr(item, "requirement"):
        value = getattr(item, "requirement")

        if value is not item:
            extracted = _requirement_text(value)
            if extracted:
                return extracted

    # Dictionary representation
    if isinstance(item, dict):
        if "requirement" in item:
            return _requirement_text(item["requirement"])

        if "text" in item:
            return str(item["text"]).strip()

        if "name" in item:
            return str(item["name"]).strip()

        return str(item).strip()

    # Pydantic model
    if hasattr(item, "model_dump") and callable(item.model_dump):
        try:
            return _requirement_text(item.model_dump())
        except Exception:
            pass

    # Pydantic v1
    if hasattr(item, "dict") and callable(item.dict):
        try:
            return _requirement_text(item.dict())
        except Exception:
            pass

    # Generic Python object
    if hasattr(item, "__dict__"):
        data = vars(item)

        if "requirement" in data:
            return _requirement_text(data["requirement"])

        if "text" in data:
            return str(data["text"]).strip()

    return str(item).strip()


def _serialize_for_json(value):
    """
    Convert arbitrary pipeline objects into JSON-serializable values.

    This is intentionally local to resume_generator because the
    tailoring pipeline can return dictionaries containing objects
    that are not directly JSON serializable.
    """

    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {
            str(key): _serialize_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _serialize_for_json(item)
            for item in value
        ]

    if hasattr(value, "model_dump") and callable(value.model_dump):
        try:
            return _serialize_for_json(value.model_dump())
        except Exception:
            pass

    if hasattr(value, "dict") and callable(value.dict):
        try:
            return _serialize_for_json(value.dict())
        except Exception:
            pass

    if hasattr(value, "__dict__"):
        return {
            str(key): _serialize_for_json(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }

    return str(value)


def _tailored_resume_text(tailored) -> str:
    """
    Convert the structured tailored resume into searchable text
    for ATS keyword scoring.

    ATS scoring requires a string, while the tailoring pipeline
    normally returns a structured dictionary.
    """

    if isinstance(tailored, str):
        return tailored

    serialized = _serialize_for_json(tailored)

    return json.dumps(
        serialized,
        ensure_ascii=False,
    )


# ============================================================
# PAGE OVERFLOW DIAGNOSTICS
# ============================================================

def _content_breakdown(tailored: dict) -> str:
    """
    Build a human-readable breakdown of section sizes, so a
    page-overflow can be diagnosed without re-running the LLM.
    """

    if not isinstance(tailored, dict):
        return "No tailored resume content available.\n"

    lines = []

    summary = str(
        tailored.get("summary", "") or ""
    )

    lines.append(
        f"Summary: {len(summary.split())} words"
    )

    education = tailored.get("education", [])

    if isinstance(education, list):
        lines.append(
            f"Education entries: {len(education)}"
        )

    skills = tailored.get("skills", {})

    categories = (
        skills.get("categories", {})
        if isinstance(skills, dict)
        else {}
    )

    if isinstance(categories, dict):
        lines.append(
            f"Skill categories: {len(categories)}"
        )

        for name, values in categories.items():
            count = (
                len(values)
                if isinstance(values, list)
                else 0
            )

            lines.append(
                f"  - {name}: {count} skills"
            )

    experience = tailored.get("experience", [])

    if isinstance(experience, list):
        lines.append("Experience:")

        for item in experience:
            if not isinstance(item, dict):
                continue

            bullets = item.get("bullets", [])

            bullet_count = (
                len(bullets)
                if isinstance(bullets, list)
                else 0
            )

            company = item.get(
                "company",
                "(unknown)",
            )

            lines.append(
                f"  - {company}: {bullet_count} bullets"
            )

    projects = tailored.get("projects", [])

    if isinstance(projects, list):
        lines.append(
            f"Projects: {len(projects)}"
        )

        for item in projects:
            if not isinstance(item, dict):
                continue

            bullets = item.get("bullets", [])

            bullet_count = (
                len(bullets)
                if isinstance(bullets, list)
                else 0
            )

            name = item.get(
                "name",
                "(unknown)",
            )

            lines.append(
                f"  - {name}: {bullet_count} bullets"
            )

    certifications = tailored.get(
        "certifications",
        [],
    )

    if isinstance(certifications, list):
        lines.append(
            f"Certifications: {len(certifications)}"
        )

    return "\n".join(lines) + "\n"


def _write_page_overflow_report(
    tailored: dict,
    tex_output_path: Path,
    pdf_path: Path,
    page_count: int,
) -> Path:
    """
    Save a diagnostic report next to the generated PDF/tex so
    overflow can be inspected and trimmed.
    """

    report_path = pdf_path.with_name(
        pdf_path.stem
        + "_page_overflow_report.txt"
    )

    report_lines = [
        "PAGE OVERFLOW REPORT",
        "=====================",
        f"Pages detected: {page_count} (target: 1)",
        f"PDF:  {pdf_path}",
        f"TeX:  {tex_output_path}",
        "",
        "Content breakdown:",
        "-------------------",
        _content_breakdown(tailored),
        "Suggested next steps:",
        "----------------------",
        "- Trim the longest experience/project bullets.",
        "- Reduce skill categories/items if several are only loosely relevant.",
        "- Shorten the summary if it is near or above the 75-word target.",
        "- Re-run generation; the PDF above reflects the current content.",
    ]

    report_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    return report_path


# ============================================================
# ITERATIVE REFINEMENT
# ============================================================

def _attempt_has_issues(
    page_count,
    evidence_flags,
    ats_score,
) -> bool:
    """
    An attempt is acceptable only if it:
      - fits on one page
      - has no unsupported-claim flags
      - has no missing required keywords
    """

    if page_count != 1:
        return True

    if evidence_flags:
        return True

    if (
        ats_score is not None
        and getattr(
            ats_score,
            "required_missing",
            0,
        )
    ):
        return True

    return False


def _build_feedback(
    page_count,
    evidence_flags,
    ats_score,
) -> str:
    """
    Turn one failed attempt's diagnostics into feedback for the
    next tailoring attempt.
    """

    lines = []

    if page_count is not None and page_count != 1:
        lines.append(
            f"- The resume was {page_count} page(s) long; "
            "it must fit exactly one page. Shorten bullets, "
            "reduce skill categories, or tighten the summary."
        )

    if evidence_flags:
        lines.append(
            "- The following bullets could not be verified "
            "against the MASTER RESUME and must be rewritten "
            "using only MASTER RESUME facts or removed. "
            "Do not invent replacements:"
        )

        max_flags_shown = 8

        for flag in evidence_flags[:max_flags_shown]:
            reasons = "; ".join(
                getattr(
                    flag,
                    "reasons",
                    [],
                )
                or []
            )

            lines.append(
                f'    [{flag.source_name}] '
                f'"{flag.bullet}" -- {reasons}'
            )

        if len(evidence_flags) > max_flags_shown:
            lines.append(
                f"    ... and "
                f"{len(evidence_flags) - max_flags_shown} "
                "more flagged bullet(s)."
            )

    if (
        ats_score is not None
        and getattr(
            ats_score,
            "required_missing",
            0,
        )
    ):
        lines.append(
            "- The following REQUIRED job-description "
            "keywords are not reflected anywhere in the resume. "
            "Where genuinely supported by the MASTER RESUME, "
            "incorporate them naturally. Do not fabricate "
            "experience or skills:"
        )

        for keyword in (
            ats_score.missing_keywords or []
        )[:10]:
            lines.append(
                f"    - {keyword}"
            )

    return "\n".join(lines)


# ============================================================
# LOAD MASTER RESUME
# ============================================================

def load_master_resume(
    path: Path = None,
) -> dict:
    path = (
        path
        or config.MASTER_RESUME_PATH
    )

    path = Path(path).resolve()

    if not path.exists():
        raise FileNotFoundError(
            "Master resume not found:\n"
            + str(path)
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as f:
        resume = yaml.safe_load(f)

    if not isinstance(
        resume,
        dict,
    ):
        raise RuntimeError(
            "Master resume YAML must contain "
            "a dictionary/object."
        )

    return resume


# ============================================================
# GENERATE RESUME
# ============================================================

def generate_resume(
    job_description: str,
    company: str = "",
    role: str = "",
    master_resume_path: Path = None,
    strict_one_page: bool = True,
    max_iterations: int = None,
) -> Path:
    """
    Full pipeline:

        1. Analyze JD
        2. Match evidence
        3. Tailor resume
        4. Score ATS
        5. Validate evidence
        6. Render LaTeX
        7. Compile PDF

    Iterative refinement:
      max_iterations controls how many tailoring attempts are made.

    If the final PDF exceeds one page:
      - PDF and TeX are retained
      - diagnostic report is written
      - strict_one_page=True raises RuntimeError
      - strict_one_page=False returns the PDF
    """

    if not isinstance(
        job_description,
        str,
    ):
        raise TypeError(
            "job_description must be a string."
        )

    if not job_description.strip():
        raise ValueError(
            "Job description cannot be empty."
        )

    if max_iterations is None:
        max_iterations = (
            config.MAX_TAILOR_ITERATIONS
        )

    max_iterations = max(
        1,
        int(max_iterations),
    )

    # --------------------------------------------------------
    # Load master resume
    # --------------------------------------------------------

    master_resume = load_master_resume(
        master_resume_path
    )

    # --------------------------------------------------------
    # Analyze JD
    # --------------------------------------------------------

    print(
        "[1/4] Analyzing job description..."
    )

    jd_analysis = extract_requirements(
        job_description
    )

    # Match the extracted requirements against the master
    # resume while preserving compatibility with mocks/tests
    # that may return a list.
    jd_requirements = match_evidence(
        jd_analysis,
        master_resume,
    )

    if isinstance(
        jd_analysis,
        JDAnalysis,
    ):
        print_analysis(
            jd_analysis
        )

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    slug_parts = [
        p
        for p in (
            company,
            role,
        )
        if p
    ]

    slug = (
        _slugify(
            "_".join(slug_parts)
        )
        if slug_parts
        else "resume"
    )

    filename_stem = (
        f"{slug}_{timestamp}"
    )

    tex_output_path = (
        config.OUTPUT_TEX_DIR
        / f"{filename_stem}.tex"
    )

    # --------------------------------------------------------
    # Tailor with retry loop
    # --------------------------------------------------------

    feedback = None
    tailored = None
    pdf_path = None
    page_count = None

    for attempt in range(
        1,
        max_iterations + 1,
    ):

        if max_iterations > 1:
            print(
                f"[2/4] Tailoring resume "
                f"(attempt {attempt}/{max_iterations})..."
            )
        else:
            print(
                "[2/4] Tailoring resume..."
            )

        if feedback:
            tailored = tailor_resume(
                master_resume,
                job_description,
                jd_requirements,
                feedback=feedback,
            )
        else:
            tailored = tailor_resume(
                master_resume,
                job_description,
                jd_requirements,
            )

        # ----------------------------------------------------
        # ATS SCORE
        # ----------------------------------------------------

        def _requirement_text(item):
            """Extract plain requirement text from requirement objects."""

            if isinstance(item, str):
                return item.strip()

            # EvidenceMatch -> JDRequirement
            requirement = getattr(item, "requirement", None)

            if requirement is not None:
                if isinstance(requirement, str):
                    return requirement.strip()

                nested = getattr(requirement, "requirement", None)

                if nested is not None:
                    return str(nested).strip()

                text = getattr(requirement, "text", None)

                if text is not None:
                    return str(text).strip()

                return str(requirement).strip()

            text = getattr(item, "text", None)

            if text is not None:
                return str(text).strip()

            return str(item).strip()


        def _tailored_resume_text(value):
            """Convert a structured tailored resume into searchable text."""

            if isinstance(value, str):
                return value

            if isinstance(value, dict):
                return json.dumps(
                    value,
                    ensure_ascii=False,
                    default=lambda obj: (
                        obj.model_dump()
                        if hasattr(obj, "model_dump")
                        else vars(obj)
                        if hasattr(obj, "__dict__")
                        else str(obj)
                    ),
                )

            if hasattr(value, "model_dump"):
                return json.dumps(
                    value.model_dump(),
                    ensure_ascii=False,
                )

            if hasattr(value, "__dict__"):
                return json.dumps(
                    vars(value),
                    ensure_ascii=False,
                    default=str,
                )

            return str(value)


        tailored_text = _tailored_resume_text(tailored)

        required_keywords = []

        for item in jd_requirements or []:
            requirement = _requirement_text(item)

            if requirement:
                required_keywords.append(requirement)

        # Remove duplicates while preserving order.
        seen_keywords = set()
        unique_keywords = []

        for keyword in required_keywords:
            key = keyword.lower()

            if key not in seen_keywords:
                seen_keywords.add(key)
                unique_keywords.append(keyword)

        required_keywords = unique_keywords

        # IMPORTANT:
        # Use positional arguments here because existing tests/mocks
        # monkeypatch score_keyword_coverage with positional lambdas.
        ats_score = score_keyword_coverage(
            tailored_text,
            required_keywords,
        )

        # ----------------------------------------------------
        # Evidence validation
        # ----------------------------------------------------

        evidence_flags = flag_unsupported_bullets(
            tailored,
            master_resume,
        )

        total_bullets = sum(
            len(item.get("bullets", []))
            for section in (
                "experience",
                "projects",
            )
            for item in tailored.get(
                section,
                [],
            )
            if (
                isinstance(item, dict)
                and isinstance(
                    item.get(
                        "bullets",
                        [],
                    ),
                    list,
                )
            )
        )

        print_evidence_check(
            evidence_flags,
            total_bullets,
        )

        # ----------------------------------------------------
        # Render LaTeX
        # ----------------------------------------------------

        print(
            "[3/4] Rendering LaTeX -> "
            f"{tex_output_path}"
        )

        render_latex(
            tailored,
            config.RESUME_TEMPLATE_PATH,
            tex_output_path,
        )

        # ----------------------------------------------------
        # Compile PDF
        # ----------------------------------------------------

        print(
            "[4/4] Compiling PDF..."
        )

        pdf_path = compile_pdf(
            tex_output_path,
            config.OUTPUT_PDF_DIR,
        )

        page_count = get_pdf_page_count(
            pdf_path
        )

        # ----------------------------------------------------
        # Decide whether retry is necessary
        # ----------------------------------------------------

        has_issues = _attempt_has_issues(
            page_count,
            evidence_flags,
            ats_score,
        )

        if (
            not has_issues
            or attempt >= max_iterations
        ):
            break

        print(
            f"Attempt {attempt}/{max_iterations} "
            "had issues; retrying with feedback..."
        )

        feedback = _build_feedback(
            page_count,
            evidence_flags,
            ats_score,
        )

    # --------------------------------------------------------
    # One-page enforcement
    # --------------------------------------------------------

    if page_count != 1:

        report_path = _write_page_overflow_report(
            tailored,
            tex_output_path,
            pdf_path,
            page_count,
        )

        message = (
            "Generated resume exceeds one page: "
            f"{page_count} pages detected.\n"
            f"PDF (kept on disk):  {pdf_path}\n"
            f"Diagnostic report:   {report_path}"
        )

        if strict_one_page:
            raise RuntimeError(
                message
            )

        print(
            f"WARNING: {message}"
        )

    print(
        f"Done: {pdf_path}"
    )

    return pdf_path
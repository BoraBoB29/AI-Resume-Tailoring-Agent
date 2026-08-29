"""
Phase-1 resume generation pipeline.

JOB DESCRIPTION
        ↓
Mistral JD-aware tailoring
        ↓
Protected master resume facts
        ↓
Validated tailored resume
        ↓
LaTeX
        ↓
PDF
"""

import re
from datetime import datetime
from pathlib import Path

import yaml

from src import config
from src.ats_scorer import print_ats_score, score_keyword_coverage
from src.evidence_matcher import match_evidence
from src.jd_analyzer import extract_requirements, print_analysis
from src.llm_tailor import tailor_resume
from src.latex_renderer import render_latex
from src.pdf_compiler import compile_pdf, get_pdf_page_count
from src.unsupported_claims import flag_unsupported_bullets, print_evidence_check


# ============================================================
# SLUGIFY
# ============================================================

def _slugify(
    text: str
) -> str:

    text = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        text.strip()
    ).strip("_")

    return (
        text.lower()
        or "role"
    )


# ============================================================
# PAGE OVERFLOW DIAGNOSTICS
# ============================================================

def _content_breakdown(tailored: dict) -> str:
    """
    Build a human-readable breakdown of section sizes, so a page-overflow
    can be diagnosed (and trimmed) without re-running the LLM.
    """

    if not isinstance(tailored, dict):
        return "No tailored resume content available.\n"

    lines = []

    summary = str(tailored.get("summary", "") or "")
    lines.append(
        f"Summary: {len(summary.split())} words"
    )

    education = tailored.get("education", [])
    if isinstance(education, list):
        lines.append(f"Education entries: {len(education)}")

    skills = tailored.get("skills", {})
    categories = (
        skills.get("categories", {})
        if isinstance(skills, dict)
        else {}
    )
    if isinstance(categories, dict):
        lines.append(f"Skill categories: {len(categories)}")
        for name, values in categories.items():
            count = len(values) if isinstance(values, list) else 0
            lines.append(f"  - {name}: {count} skills")

    experience = tailored.get("experience", [])
    if isinstance(experience, list):
        lines.append("Experience:")
        for item in experience:
            if not isinstance(item, dict):
                continue
            bullets = item.get("bullets", [])
            bullet_count = len(bullets) if isinstance(bullets, list) else 0
            company = item.get("company", "(unknown)")
            lines.append(f"  - {company}: {bullet_count} bullets")

    projects = tailored.get("projects", [])
    if isinstance(projects, list):
        lines.append(f"Projects: {len(projects)}")
        for item in projects:
            if not isinstance(item, dict):
                continue
            bullets = item.get("bullets", [])
            bullet_count = len(bullets) if isinstance(bullets, list) else 0
            name = item.get("name", "(unknown)")
            lines.append(f"  - {name}: {bullet_count} bullets computed (only bullet 1 is rendered)")

    certifications = tailored.get("certifications", [])
    if isinstance(certifications, list):
        lines.append(f"Certifications: {len(certifications)}")

    return "\n".join(lines) + "\n"


def _write_page_overflow_report(
    tailored: dict,
    tex_output_path: Path,
    pdf_path: Path,
    page_count: int,
) -> Path:
    """
    Save a diagnostic report next to the generated PDF/tex so an overflow
    can be inspected and trimmed, instead of discarding the whole run.
    """

    report_path = pdf_path.with_name(
        pdf_path.stem + "_page_overflow_report.txt"
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
        "- Trim the longest experience/project bullets (see counts above).",
        "- Reduce skill categories/items if several are only loosely relevant.",
        "- Shorten the summary if it is near or above the 75-word target.",
        "- Re-run generation; the PDF above reflects the current (overflowing) content.",
    ]

    report_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    return report_path


# ============================================================
# ITERATIVE REFINEMENT
# ============================================================

def _attempt_has_issues(page_count, evidence_flags, ats_score) -> bool:
    """
    An attempt is considered acceptable (no retry needed) only if it fits
    one page, has no unsupported-claim flags, and covers every REQUIRED JD
    keyword the ATS scorer found evidence for elsewhere in the resume.
    Missing PREFERRED keywords alone do not trigger a retry.
    """

    if page_count != 1:
        return True

    if evidence_flags:
        return True

    if ats_score is not None and getattr(ats_score, "required_missing", 0):
        return True

    return False


def _build_feedback(page_count, evidence_flags, ats_score) -> str:
    """
    Turn one failed attempt's diagnostics into plain-text feedback for the
    next tailoring attempt's prompt (see llm_tailor._feedback_section).
    """

    lines = []

    if page_count is not None and page_count != 1:
        lines.append(
            f"- The resume was {page_count} page(s) long; it must fit "
            "exactly one page. Shorten bullets, reduce skill categories, "
            "or tighten the summary."
        )

    if evidence_flags:
        lines.append(
            "- The following bullets could not be verified against the "
            "MASTER RESUME and must be rewritten (using only MASTER RESUME "
            "facts) or removed -- do not invent replacements:"
        )
        max_flags_shown = 8
        for flag in evidence_flags[:max_flags_shown]:
            reasons = "; ".join(getattr(flag, "reasons", []) or [])
            lines.append(
                f'    [{flag.source_name}] "{flag.bullet}" -- {reasons}'
            )
        if len(evidence_flags) > max_flags_shown:
            lines.append(
                f"    ... and {len(evidence_flags) - max_flags_shown} "
                "more flagged bullet(s)."
            )

    if ats_score is not None and getattr(ats_score, "required_missing", 0):
        lines.append(
            "- The following REQUIRED job-description keywords are not "
            "reflected anywhere in the resume. Where genuinely supported "
            "by the MASTER RESUME, incorporate them naturally; do not "
            "fabricate experience or skills that aren't in the MASTER "
            "RESUME just to cover a keyword:"
        )
        for keyword in (ats_score.missing_keywords or [])[:10]:
            lines.append(f"    - {keyword}")

    return "\n".join(lines)


# ============================================================
# LOAD MASTER RESUME
# ============================================================

def load_master_resume(
    path: Path = None
) -> dict:

    path = (
        path
        or config.MASTER_RESUME_PATH
    )

    path = Path(
        path
    ).resolve()

    if not path.exists():

        raise FileNotFoundError(
            "Master resume not found:\n"
            + str(path)
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        resume = yaml.safe_load(f)

    if not isinstance(
        resume,
        dict
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
        2. Tailor resume (may retry, see below)
        3. Render LaTeX
        4. Compile PDF

    Iterative refinement:
      max_iterations controls how many tailoring attempts are made.
      Defaults to config.MAX_TAILOR_ITERATIONS (itself defaulting to 1 --
      the original single-shot behavior). When set above 1, an attempt
      that overflows one page, has unsupported-claim flags, or is missing
      REQUIRED JD keywords is fed back to the LLM as specific, factual
      feedback and retried, up to max_iterations attempts total. The last
      attempt made is always the one rendered/returned.

    If the final attempt's PDF exceeds one page:
      - The PDF and .tex files are always kept on disk (never discarded).
      - A diagnostic report is written alongside them breaking down bullet/
        section counts so the overflow can be traced and trimmed.
      - If strict_one_page is True (default), a RuntimeError is raised
        pointing at both files. If False, a warning is printed instead and
        the (overflowing) PDF path is returned.
    """

    if not job_description.strip():

        raise ValueError(
            "Job description cannot be empty."
        )

    if max_iterations is None:
        max_iterations = config.MAX_TAILOR_ITERATIONS

    max_iterations = max(1, int(max_iterations))

    # --------------------------------------------------------
    # Load master resume
    # --------------------------------------------------------

    master_resume = load_master_resume(
        master_resume_path
    )

    # --------------------------------------------------------
    # Analyze JD (once -- does not depend on tailoring attempt)
    # --------------------------------------------------------

    print("[1/4] Analyzing job description...")

    jd_requirements = extract_requirements(job_description)
    jd_requirements = match_evidence(
        jd_requirements,
        master_resume
    )
    print_analysis(jd_requirements)

    # --------------------------------------------------------
    # Filename (fixed across attempts, so each retry overwrites
    # the same .tex/.pdf rather than littering the output dir)
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    slug_parts = [
        p
        for p in (
            company,
            role
        )
        if p
    ]

    slug = (
        _slugify(
            "_".join(
                slug_parts
            )
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
    # Tailor (with retry loop)
    # --------------------------------------------------------

    feedback = None
    tailored = None
    pdf_path = None
    page_count = None

    for attempt in range(1, max_iterations + 1):

        if max_iterations > 1:
            print(f"[2/4] Tailoring resume (attempt {attempt}/{max_iterations})...")
        else:
            print("[2/4] Tailoring resume...")

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
                jd_requirements
            )

        ats_score = score_keyword_coverage(
            tailored,
            jd_requirements
        )
        print_ats_score(ats_score)

        evidence_flags = flag_unsupported_bullets(
            tailored,
            master_resume
        )
        total_bullets = sum(
            len(item.get("bullets", []))
            for section in ("experience", "projects")
            for item in tailored.get(section, [])
            if isinstance(item, dict) and isinstance(item.get("bullets", []), list)
        )
        print_evidence_check(evidence_flags, total_bullets)

        print(
            f"[3/4] Rendering LaTeX -> "
            f"{tex_output_path}"
        )

        render_latex(
            tailored,
            config.RESUME_TEMPLATE_PATH,
            tex_output_path
        )

        print(
            "[4/4] Compiling PDF..."
        )

        pdf_path = compile_pdf(
            tex_output_path,
            config.OUTPUT_PDF_DIR
        )

        page_count = get_pdf_page_count(pdf_path)

        has_issues = _attempt_has_issues(
            page_count,
            evidence_flags,
            ats_score,
        )

        if not has_issues or attempt >= max_iterations:
            break

        print(
            f"Attempt {attempt}/{max_iterations} had issues; "
            f"retrying with feedback..."
        )
        feedback = _build_feedback(
            page_count,
            evidence_flags,
            ats_score,
        )

    # --------------------------------------------------------
    # One-page enforcement (applies to the last attempt made)
    # --------------------------------------------------------

    if page_count != 1:

        report_path = _write_page_overflow_report(
            tailored,
            tex_output_path,
            pdf_path,
            page_count,
        )

        message = (
            f"Generated resume exceeds one page: "
            f"{page_count} pages detected.\n"
            f"PDF (kept on disk):  {pdf_path}\n"
            f"Diagnostic report:   {report_path}"
        )

        if strict_one_page:
            raise RuntimeError(message)

        print(f"WARNING: {message}")

    print(
        f"Done: {pdf_path}"
    )

    return pdf_path
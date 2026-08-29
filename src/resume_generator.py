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
) -> Path:

    """
    Full pipeline:

        1. Analyze JD
        2. Tailor resume
        3. Render LaTeX
        4. Compile PDF

    If the compiled PDF exceeds one page:
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

    # --------------------------------------------------------
    # Load master resume
    # --------------------------------------------------------

    master_resume = load_master_resume(
        master_resume_path
    )

    # --------------------------------------------------------
    # Analyze JD and tailor
    # --------------------------------------------------------

    print("[1/4] Analyzing job description...")

    jd_requirements = extract_requirements(job_description)
    jd_requirements = match_evidence(
        jd_requirements,
        master_resume
    )
    print_analysis(jd_requirements)

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

    # --------------------------------------------------------
    # LaTeX path
    # --------------------------------------------------------

    tex_output_path = (
        config.OUTPUT_TEX_DIR
        / f"{filename_stem}.tex"
    )

    print(
        f"[2/4] Rendering LaTeX -> "
        f"{tex_output_path}"
    )

    render_latex(
        tailored,
        config.RESUME_TEMPLATE_PATH,
        tex_output_path
    )

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    print(
        "[3/4] Compiling PDF..."
    )

    pdf_path = compile_pdf(
        tex_output_path,
        config.OUTPUT_PDF_DIR
    )

    page_count = get_pdf_page_count(pdf_path)

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
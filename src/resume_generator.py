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
from src.llm_tailor import tailor_resume
from src.latex_renderer import render_latex
from src.pdf_compiler import compile_pdf, get_pdf_page_count


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
) -> Path:

    """
    Full pipeline:

        1. Analyze JD
        2. Tailor resume
        3. Render LaTeX
        4. Compile PDF
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
    # Tailor
    # --------------------------------------------------------

    print(
        "[1/3] Analyzing JD and tailoring resume..."
    )

    tailored = tailor_resume(
        master_resume,
        job_description
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
        f"[2/3] Rendering LaTeX -> "
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
        "[3/3] Compiling PDF..."
    )

    pdf_path = compile_pdf(
        tex_output_path,
        config.OUTPUT_PDF_DIR
    )

    page_count = get_pdf_page_count(pdf_path)

    if page_count != 1:
        raise RuntimeError(
            f"Generated resume exceeds one page: "
            f"{page_count} pages detected."
        )

    print(
        f"Done: {pdf_path}"
    )

    return pdf_path
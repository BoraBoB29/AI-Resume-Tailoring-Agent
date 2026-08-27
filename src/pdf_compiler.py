"""
Compiles a .tex file to PDF using either 'tectonic' (recommended -- self
contained, no separate TeX Live install needed) or 'pdflatex' (needs a full
TeX Live / MiKTeX install on PATH).

On failure, the compiler's log is saved next to the .tex file so you can
debug exactly what went wrong.
"""
import shutil
import subprocess
from pathlib import Path

from pypdf import PdfReader

from src import config


class LatexCompilationError(RuntimeError):
    pass


def get_pdf_page_count(pdf_path: Path) -> int:
    """Return the number of pages in an existing PDF."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        return len(PdfReader(str(pdf_path)).pages)
    except Exception as exc:
        raise ValueError(f"Invalid PDF: {pdf_path}") from exc


def _check_engine_available(engine: str):
    if shutil.which(engine) is None:
        raise LatexCompilationError(
            f"'{engine}' was not found on PATH. Install it first:\n"
            f"  - tectonic: https://tectonic-typesetting.github.io/en-US/install.html\n"
            f"  - or set LATEX_ENGINE=pdflatex in .env and install TeX Live / MiKTeX."
        )


def compile_pdf(tex_path: Path, output_pdf_dir: Path, engine: str = None) -> Path:
    """
    Compile the given .tex file to PDF. Returns the path to the resulting PDF.
    Raises LatexCompilationError on failure.
    """
    engine = engine or config.LATEX_ENGINE
    _check_engine_available(engine)
    output_pdf_dir.mkdir(parents=True, exist_ok=True)

    if engine == "tectonic":
        cmd = ["tectonic", "--outdir", str(output_pdf_dir), str(tex_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        pdf_path = output_pdf_dir / (tex_path.stem + ".pdf")
        log_text = result.stdout + result.stderr

    elif engine == "pdflatex":
        # Run twice to resolve any cross-references (harmless for a simple resume,
        # but keeps this robust if the template grows a table of contents etc.)
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", str(output_pdf_dir),
            str(tex_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        subprocess.run(cmd, capture_output=True, text=True)  # 2nd pass
        pdf_path = output_pdf_dir / (tex_path.stem + ".pdf")
        log_text = result.stdout + result.stderr

    else:
        raise LatexCompilationError(f"Unknown LATEX_ENGINE: {engine!r}")

    if not pdf_path.exists():
        log_file = output_pdf_dir / (tex_path.stem + "_compile_error.log")
        log_file.write_text(log_text, encoding="utf-8")
        raise LatexCompilationError(
            f"PDF compilation failed. See log at {log_file}"
        )

    return pdf_path

"""
Central configuration for the resume-tailoring pipeline.
Loads environment variables and defines fixed project paths.
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# --- API / model config -----------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
LATEX_ENGINE = os.getenv("LATEX_ENGINE", "pdflatex")  # "tectonic" or "pdflatex"

# --- Paths -------------------------------------------------------------------
DATA_DIR = PROJECT_ROOT / "data"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_TEX_DIR = OUTPUT_DIR / "tex"
OUTPUT_PDF_DIR = OUTPUT_DIR / "pdf"

MASTER_RESUME_PATH = DATA_DIR / "master_resume.yaml"
RESUME_TEMPLATE_PATH = TEMPLATES_DIR / "resume_template.tex"

for d in (OUTPUT_TEX_DIR, OUTPUT_PDF_DIR):
    d.mkdir(parents=True, exist_ok=True)

if not ANTHROPIC_API_KEY:
    # Don't crash on import (e.g. during testing of non-LLM parts),
    # but calls to the LLM tailor module will fail loudly with a clear message.
    pass

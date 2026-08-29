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
LATEX_ENGINE = os.getenv("LATEX_ENGINE", "pdflatex")  # "tectonic" or "pdflatex"

# Maximum tailoring attempts per resume generation. 1 reproduces the
# original single-shot behavior; >1 enables automatic re-prompting with
# feedback (unsupported claims, missing JD keywords, page overflow) on
# failed attempts. See src/resume_generator.py.
MAX_TAILOR_ITERATIONS = int(os.getenv("MAX_TAILOR_ITERATIONS", "1"))

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


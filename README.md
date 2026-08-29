# AI Resume Tailoring Agent

An AI-powered resume tailoring system that converts a job description and a candidate's master resume into a tailored, ATS-friendly, one-page PDF resume.

**Status: Phase 2.** Phase 1 (reliable resume generation and formatting) and Phase 2 (intelligent job analysis, resume scoring, evidence matching, and iterative self-correction) are both implemented.

---

# Pipeline

```
Job Description
        │
        ▼
JD Requirement Extraction  (src/jd_analyzer.py)
        │
        ▼
Evidence Matching against Master Resume  (src/evidence_matcher.py)
        │
        ▼
LLM Resume Tailoring  (src/llm_tailor.py)
        │
        ├──▶ ATS Keyword Coverage Scoring  (src/ats_scorer.py)
        ├──▶ Unsupported-Claim Detection  (src/unsupported_claims.py)
        │
        │    If issues found and retries remain, feed specific,
        │    factual feedback back into another tailoring attempt.
        │    (opt-in; see "Iterative refinement" below)
        │
        ▼
Pydantic Validation  (src/schema.py)
        │
        ▼
LaTeX Rendering  (src/latex_renderer.py + templates/resume_template.tex)
        │
        ▼
PDF Compilation  (src/pdf_compiler.py)
        │
        ▼
One-page Enforcement (page count is checked; see below)
        │
        ▼
Tailored, ATS-checked, one-page PDF Resume
```

---

# Features

**Phase 1 — generation**
- Job-description-based resume tailoring via Mistral, with retry/backoff on transient API errors (`src/mistral_client.py`)
- Evidence-grounded resume generation — the master resume is the only source of factual truth; the LLM is instructed never to invent employers, dates, technologies, metrics, or certifications
- Dynamic, generalized skill categorization (near-duplicate LLM category names are merged into a fixed, role-neutral vocabulary, capped at 6 categories)
- Experience selection and rewriting, with a deterministic bullet-count floor/cap per employer
- Project selection (exactly 3, always drawn from canonical master-resume projects, never invented)
- Education rendering, including GPA and free-form details (e.g. secondary-school percentages)
- Certification handling (accepts both structured objects and free-text strings from the LLM, normalizes both)
- Pydantic schema validation of every LLM response
- LaTeX resume generation and PDF compilation (`pdflatex` or `tectonic`)
- **One-page enforcement**: the compiled PDF's page count is checked. On overflow, the PDF and `.tex` are always kept on disk (never discarded) and a `*_page_overflow_report.txt` is written next to them, breaking down bullet/section counts so the overflow can be diagnosed without re-running the LLM. Use `--allow-multi-page` to get a warning instead of a hard failure.

**Phase 2 — analysis, scoring, and self-correction**
- **JD requirement extraction** (`src/jd_analyzer.py`): turns a job description into a structured list of atomic requirements (required / preferred / implicit), via an LLM extraction pass plus a deterministic backstop splitter for common list-like phrasing.
- **Evidence matching** (`src/evidence_matcher.py`): links each JD requirement to the specific master-resume field(s) that support it, before tailoring even happens.
- **ATS keyword coverage scoring** (`src/ats_scorer.py`): a fully deterministic (no LLM) score of how well the *tailored* resume covers required/preferred JD keywords, with a missing-keyword list.
- **Unsupported-claim detection** (`src/unsupported_claims.py`): deterministic post-hoc check flagging any generated experience/project bullet whose technologies, metrics, or overall content aren't adequately traceable back to the master resume — catches subtle fabrication the prompt-level guardrails alone might miss.
- **Iterative refinement** (`src/resume_generator.py`, opt-in via `--max-iterations` / `MAX_TAILOR_ITERATIONS`): when enabled, a failed attempt (page overflow, unsupported-claim flags, or missing *required* JD keywords) is automatically turned into specific feedback and fed back into another tailoring attempt, up to the configured number of attempts. Defaults to 1 attempt (original single-shot behavior) unless explicitly raised.

---

# Usage

```bash
# Original single-shot generation (default)
python main.py --jd-file data/job_description.txt --company "Acme" --role "Data Analyst"

# Allow the pipeline to retry itself up to 2 times if the first attempt
# has unsupported claims, missing required keywords, or overflows one page
python main.py --jd-file data/job_description.txt --max-iterations 2

# Don't fail on a multi-page result -- keep the PDF and warn instead
python main.py --jd-file data/job_description.txt --allow-multi-page
```

Run `python main.py --help` for the full flag list.

---

# Architecture

## Input

The system uses two primary inputs:

1. A job description
2. A master resume stored locally as YAML

The master resume is the candidate's factual source of truth.

The actual master resume is intentionally excluded from GitHub because it contains personal information (see `.gitignore`).

A safe example is provided at:

```text
data/master_resume.example.yaml
```

## Configuration

Copy `.env.example` to `.env` and fill in `MISTRAL_API_KEY`. All other variables are optional and documented inline in `.env.example` (model, LaTeX engine, request timeout/retry tuning, and the iterative-refinement attempt limit).

## Output

Generated `.tex` files are written to `output/tex/`, compiled PDFs to `output/pdf/`. Both are gitignored. On a one-page overflow that isn't resolved, a matching `*_page_overflow_report.txt` is written alongside the PDF.

---

# Tests

```bash
pip install -r requirements.txt
python -m pytest
```

The suite is fully offline and deterministic — no test makes a real API call. A handful of standalone scripts (`test_mistral.py`, `test_mistral_models.py`, `test_tailor.py`, `test_latex.py`, `test_yaml.py`) are manual smoke scripts that *do* call the real Mistral API or compile real LaTeX; they detect when they're running under `pytest` and skip themselves automatically, and are meant to be run directly (e.g. `python test_mistral.py`) when you specifically want to exercise live API/toolchain access.

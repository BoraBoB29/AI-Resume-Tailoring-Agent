# Job Apply Bot — Phase 1: Tailored Resume Generator

Given a job description, this generates a resume tailored to it, written in LaTeX,
and compiled to a ready-to-submit PDF.

## Folder structure

```
job_apply_bot/
├── data/
│   └── master_resume.yaml       # your full, factual resume (source of truth)
├── templates/
│   └── resume_template.tex       # LaTeX template (Jinja2-rendered, LaTeX-safe delimiters)
├── src/
│   ├── config.py                 # env vars + paths
│   ├── schema.py                 # pydantic schema for tailored resume
│   ├── llm_tailor.py              # calls Claude to tailor content to a JD
│   ├── latex_renderer.py          # renders tailored data into .tex
│   ├── pdf_compiler.py            # compiles .tex -> .pdf
│   └── resume_generator.py        # orchestrates the pipeline
├── output/
│   ├── tex/                      # generated .tex files land here
│   └── pdf/                      # generated .pdf files land here
├── main.py                        # CLI entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## Setup

1. Activate your existing venv:
   ```bash
   # Windows (VS Code terminal)
   bora\Scripts\activate
   # macOS/Linux
   source bora/bin/activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install a LaTeX engine (required — not a pip package):
   - **Recommended: [Tectonic](https://tectonic-typesetting.github.io/en-US/install.html)**
     — self-contained, downloads packages on demand, no multi-GB TeX Live install.
     - Windows: `winget install tectonic-typesetting.tectonic` (or via `cargo install tectonic`, or `conda install -c conda-forge tectonic`)
     - macOS: `brew install tectonic`
     - Linux: see install docs above
   - **Alternative:** install a full TeX distribution (TeX Live or MiKTeX) and set
     `LATEX_ENGINE=pdflatex` in `.env`.

4. Set up your API key:
   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # macOS/Linux
   ```
   Then edit `.env` and add your `ANTHROPIC_API_KEY`.

5. Fill in `data/master_resume.yaml` with your real, complete experience.
   Include **more bullets than you'd normally put on one resume** — the LLM
   selects and reweights from this, it doesn't invent new content.

## Usage

```bash
python main.py --jd-file path/to/job_description.txt --company "Acme" --role "Backend Engineer"
```

or pass the JD text directly:

```bash
python main.py --jd "Full job description text here..." --company "Acme" --role "Backend Engineer"
```

Output: a compiled PDF in `output/pdf/`, and the intermediate `.tex` in `output/tex/`
(useful if you want to hand-tweak formatting before applying).

## How factual accuracy is protected

- `llm_tailor.py`'s system prompt explicitly forbids inventing employers, titles,
  dates, or metrics not present in `master_resume.yaml`. The LLM may only select,
  reorder, and reword existing content to match the job description's language.
- Output is forced into strict JSON and validated against `schema.py` (pydantic)
  before it's allowed anywhere near the LaTeX template — malformed output is
  retried automatically (up to 3 attempts) rather than silently producing a bad PDF.
- Always skim the generated PDF before submitting anywhere — treat the LLM as a
  drafting assistant, not a final authority on your own resume.

## Notes for later phases

Auto-submitting applications on LinkedIn/Indeed/company ATS sites (Workday,
Greenhouse, Lever, etc.) is a separate, harder problem — it involves browser
automation, handling arbitrary custom questions, and each platform's own terms
of service on automated activity are worth checking before you point a bot at them.
This phase intentionally stops at "produce a submission-ready PDF" so you have a
clean, tested building block before adding that layer.

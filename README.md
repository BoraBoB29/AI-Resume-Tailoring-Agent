# AI Resume Tailoring Agent

An AI-powered resume tailoring system that converts a job description and a candidate's master resume into a tailored, ATS-friendly, one-page PDF resume.

The project is currently in **Phase 1**, focused on reliable resume generation and formatting. Phase 2 will extend the system toward intelligent job analysis, resume scoring, evidence matching, and application workflow automation.

---

# Phase 1 — Tailored Resume Generator

The current pipeline is:

Job Description
        ↓
LLM Resume Tailoring
        ↓
Pydantic Validation
        ↓
Structured Resume
        ↓
LaTeX Rendering
        ↓
PDF Compilation
        ↓
One-page Resume

---

# Features

- Job-description-based resume tailoring
- Evidence-grounded resume generation
- Dynamic skill categorization
- Experience selection and rewriting
- Project selection
- Education rendering
- Certification handling
- Pydantic schema validation
- LaTeX resume generation
- PDF compilation
- One-page resume formatting
- ATS-oriented keyword alignment
- Protected master-resume source of truth

---

# Architecture

## Input

The system uses two primary inputs:

1. A job description
2. A master resume stored locally as YAML

The master resume is the candidate's factual source of truth.

The actual master resume is intentionally excluded from GitHub because it contains personal information.

A safe example is provided at:

```text
data/master_resume.example.yaml
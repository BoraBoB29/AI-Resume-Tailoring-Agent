import pytest
from pypdf import PdfWriter

from src import resume_generator
from src.pdf_compiler import get_pdf_page_count


def write_pdf(path, page_count):
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as file:
        writer.write(file)


def test_get_pdf_page_count_returns_one_for_one_page_pdf(tmp_path):
    pdf_path = tmp_path / "one-page.pdf"
    write_pdf(pdf_path, 1)

    assert get_pdf_page_count(pdf_path) == 1


def test_get_pdf_page_count_returns_multi_page_count(tmp_path):
    pdf_path = tmp_path / "multi-page.pdf"
    write_pdf(pdf_path, 2)

    assert get_pdf_page_count(pdf_path) == 2


def test_get_pdf_page_count_rejects_missing_pdf(tmp_path):
    with pytest.raises(FileNotFoundError, match="PDF not found"):
        get_pdf_page_count(tmp_path / "missing.pdf")


def test_get_pdf_page_count_rejects_invalid_pdf(tmp_path):
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("not a PDF", encoding="ascii")

    with pytest.raises(ValueError, match="Invalid PDF"):
        get_pdf_page_count(pdf_path)


def _patch_pipeline(monkeypatch, pdf_path, tailored=None):
    monkeypatch.setattr(resume_generator, "load_master_resume", lambda path: {})
    monkeypatch.setattr(resume_generator, "extract_requirements", lambda jd: [])
    monkeypatch.setattr(resume_generator, "match_evidence", lambda reqs, master: reqs)
    monkeypatch.setattr(resume_generator, "tailor_resume", lambda master, jd, requirements: (tailored or {}))
    monkeypatch.setattr(resume_generator, "score_keyword_coverage", lambda tailored, reqs: None)
    monkeypatch.setattr(resume_generator, "print_ats_score", lambda score: None)
    monkeypatch.setattr(resume_generator, "flag_unsupported_bullets", lambda tailored, master: [])
    monkeypatch.setattr(resume_generator, "render_latex", lambda *args: None)
    monkeypatch.setattr(resume_generator, "compile_pdf", lambda *args: pdf_path)


def test_generate_resume_rejects_multi_page_output(tmp_path, monkeypatch):
    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)
    _patch_pipeline(monkeypatch, pdf_path)

    with pytest.raises(
        RuntimeError,
        match="Generated resume exceeds one page: 2 pages detected",
    ):
        resume_generator.generate_resume("test job description")


def test_generate_resume_keeps_pdf_on_multi_page_failure(tmp_path, monkeypatch):
    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)
    _patch_pipeline(monkeypatch, pdf_path)

    with pytest.raises(RuntimeError):
        resume_generator.generate_resume("test job description")

    # The PDF must never be deleted just because it overflowed one page.
    assert pdf_path.exists()


def test_generate_resume_writes_diagnostic_report_on_overflow(tmp_path, monkeypatch):
    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)
    tailored = {
        "summary": "A short summary.",
        "experience": [{"company": "Acme", "bullets": ["a", "b", "c"]}],
        "projects": [{"name": "Widget", "bullets": ["x", "y"]}],
        "skills": {"categories": {"Tools": ["Python", "SQL"]}},
    }
    _patch_pipeline(monkeypatch, pdf_path, tailored=tailored)

    with pytest.raises(RuntimeError):
        resume_generator.generate_resume("test job description")

    report_path = tmp_path / "generated_page_overflow_report.txt"
    assert report_path.exists()

    report_text = report_path.read_text(encoding="utf-8")
    assert "Acme: 3 bullets" in report_text
    assert "Widget: 2 bullets" in report_text
    assert "Tools: 2 skills" in report_text


def test_generate_resume_allows_multi_page_when_not_strict(tmp_path, monkeypatch):
    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)
    _patch_pipeline(monkeypatch, pdf_path)

    result = resume_generator.generate_resume(
        "test job description",
        strict_one_page=False,
    )

    # No exception raised, and the (overflowing) PDF path is still returned.
    assert result == pdf_path

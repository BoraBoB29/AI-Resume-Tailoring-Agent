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


def test_generate_resume_rejects_multi_page_output(tmp_path, monkeypatch):
    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)
    monkeypatch.setattr(resume_generator, "load_master_resume", lambda path: {})
    monkeypatch.setattr(resume_generator, "tailor_resume", lambda master, jd: {})
    monkeypatch.setattr(resume_generator, "render_latex", lambda *args: None)
    monkeypatch.setattr(resume_generator, "compile_pdf", lambda *args: pdf_path)

    with pytest.raises(
        RuntimeError,
        match="Generated resume exceeds one page: 2 pages detected",
    ):
        resume_generator.generate_resume("test job description")

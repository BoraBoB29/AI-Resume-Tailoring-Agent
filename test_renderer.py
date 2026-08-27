from pathlib import Path

from src.latex_renderer import render_latex


def test_render_latex_writes_resume_content(tmp_path):
    resume = {
        "contact": {
            "name": "Test Candidate",
            "email": "candidate@example.com",
            "phone": "555-0100",
            "linkedin": "linkedin.com/in/candidate",
            "location": "Pune, India",
        },
        "summary": "A concise test summary.",
        "education": [],
        "skills": {"categories": {"Tools": ["Python", "SQL"]}},
        "experience": [],
        "projects": [],
        "certifications": [],
    }
    template_path = Path("templates/resume_template.tex")
    output_path = tmp_path / "resume.tex"

    result = render_latex(resume, template_path, output_path)

    assert result == output_path
    assert output_path.exists()
    rendered = output_path.read_text(encoding="utf-8")
    assert "Test Candidate" in rendered
    assert "A concise test summary." in rendered
    assert "Python" in rendered
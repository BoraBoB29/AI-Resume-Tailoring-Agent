from pathlib import Path

from src.latex_renderer import format_education, render_latex


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


def test_format_education_keeps_gpa_and_school_percentages_intact():
    rendered = format_education([
        {
            "institution": "Symbiosis Institute of Technology",
            "degree": "B.Tech – Robotics and Automation",
            "location": "Pune, India",
            "start_date": "Aug 2022",
            "end_date": "Jun 2026",
            "gpa": "7.5/10",
        },
        {
            "institution": "City Montessori School",
            "degree": "Class XII: 95.25% | Class X: 93.00%",
            "location": "Lucknow, India",
            "start_date": "2020",
            "end_date": "2022",
        },
    ])

    assert "B.Tech – Robotics and Automation \\quad|\\quad GPA: 7.5/10" in rendered
    assert "GPA: 7.5/10\n" not in rendered
    assert "Class XII: 95.25\\% | Class X: 93.00\\%" in rendered
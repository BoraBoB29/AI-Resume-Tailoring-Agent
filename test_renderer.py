from pathlib import Path

from src.latex_renderer import format_contact, format_education, format_projects, render_latex


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


def test_format_education_renders_details_field():
    rendered = format_education([
        {
            "institution": "Example University",
            "degree": "B.Tech",
            "location": "Pune, India",
            "start_date": "2022",
            "end_date": "2026",
            "gpa": "7.5/10",
            "details": ["Class XII: 95.25%", "Class X: 93.00%"],
        },
    ])

    assert "Class XII: 95.25\\% | Class X: 93.00\\%" in rendered


def test_format_education_omits_details_block_when_empty():
    with_empty_details = format_education([
        {
            "institution": "Example University",
            "degree": "B.Tech",
            "location": "Pune, India",
            "start_date": "2022",
            "end_date": "2026",
            "details": [],
        },
    ])
    without_details_key = format_education([
        {
            "institution": "Example University",
            "degree": "B.Tech",
            "location": "Pune, India",
            "start_date": "2022",
            "end_date": "2026",
        },
    ])

    # An empty/missing details list must render identically to no details
    # at all -- no stray details line should appear either way.
    assert with_empty_details == without_details_key


def test_format_contact_renders_optional_links():
    rendered = format_contact({
        "name": "Candidate",
        "email": "candidate@example.com",
        "phone": "555-0100",
        "linkedin": "linkedin.com/in/candidate",
        "github": "github.com/candidate",
        "portfolio": "candidate.example.com",
        "location": "Pune, India",
    })

    assert "github.com/candidate" in rendered
    assert "candidate.example.com" in rendered


def test_format_contact_email_is_a_mailto_link():
    # Regression guard: a prior refactor accidentally rendered the email
    # as plain text with no mailto: link.
    rendered = format_contact({
        "name": "Candidate",
        "email": "candidate@example.com",
        "phone": "555-0100",
        "location": "Pune, India",
    })

    assert r"\href{mailto:candidate@example.com}{candidate@example.com}" in rendered


def test_format_projects_skips_entries_without_a_name_or_bullets():
    rendered = format_projects([
        {"name": "", "bullets": ["Should be skipped: no name"]},
        {"name": "No Bullets Project", "bullets": []},
        "not a dict",
        {"name": "Valid Project", "bullets": ["A real description"]},
    ])

    assert "Should be skipped" not in rendered
    assert "No Bullets Project" not in rendered
    assert "Valid Project" in rendered
    assert "A real description" in rendered


def test_format_projects_returns_empty_string_for_no_valid_projects():
    assert format_projects([]) == ""
    assert format_projects([{"name": "", "bullets": []}]) == ""


def test_format_projects_renders_multiple_bullets():
    rendered = format_projects([{
        "name": "Canonical Project",
        "bullets": ["Primary analysis", "Supporting validation", "Additional finding"],
    }])

    assert "Primary analysis" in rendered
    assert "Supporting validation" not in rendered
    assert "Additional finding" not in rendered

def test_format_contact_keeps_location_on_contact_line():
    rendered = format_contact({
        "name": "Candidate",
        "email": "candidate@example.com",
        "phone": "555-0100",
        "linkedin": "linkedin.com/in/candidate",
        "location": "Pune, India",
    })

    assert r"\href{mailto:candidate@example.com}{candidate@example.com}" in rendered
    assert r"555-0100\enspace $|$ \enspace \href{https://linkedin.com/in/candidate}" in rendered
    assert r"linkedin.com/in/candidate}\enspace $|$ \enspace Pune, India" in rendered

from src.jd_analyzer import (
    JDAnalysis,
    extract_requirements,
    analyze_job_description,
)


def test_extract_requirements():
    jd = """
    Product Manager

    Required Qualifications:
    - Product management experience
    - Python
    - SQL
    - Stakeholder management

    Preferred Qualifications:
    - SaaS experience
    - AWS
    """

    result = extract_requirements(jd)

    assert isinstance(result, JDAnalysis)

    assert "Product management experience" in result.required
    assert "Python" in result.required
    assert "SQL" in result.required
    assert "Stakeholder management" in result.required

    assert "SaaS experience" in result.preferred
    assert "AWS" in result.preferred


def test_extract_requirements_handles_bullet_markers():
    jd = """
    Requirements:
    - Python
    * SQL
    • Product Management
    """

    result = extract_requirements(jd)

    assert "Python" in result.required
    assert "SQL" in result.required
    assert "Product Management" in result.required


def test_extract_requirements_does_not_duplicate_items():
    jd = """
    Requirements:
    - Python
    - Python
    - SQL
    """

    result = extract_requirements(jd)

    assert result.required.count("Python") == 1
    assert result.required.count("SQL") == 1


def test_extract_requirements_preferred_section():
    jd = """
    Required Qualifications:
    - Python

    Preferred Qualifications:
    - AWS
    - Docker
    """

    result = extract_requirements(jd)

    assert "Python" in result.required
    assert "AWS" in result.preferred
    assert "Docker" in result.preferred


def test_extract_requirements_empty_description():
    try:
        extract_requirements("")
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_extract_requirements_invalid_input():
    try:
        extract_requirements(None)
        assert False, "Expected TypeError"
    except TypeError:
        pass


def test_analyze_job_description_alias():
    jd = """
    Requirements:
    - Python
    - SQL
    """

    result = analyze_job_description(jd)

    assert isinstance(result, JDAnalysis)
    assert "Python" in result.required
    assert "SQL" in result.required
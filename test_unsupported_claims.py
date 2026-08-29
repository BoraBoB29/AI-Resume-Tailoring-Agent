from src.unsupported_claims import flag_unsupported_bullets


MASTER_RESUME = {
    "skills": {"categories": {"Data Analytics": ["SQL", "Python", "Power BI"]}},
    "experience": [
        {
            "company": "Example Co",
            "title": "Analyst",
            "bullets": [
                "Built SQL dashboards for recurring stakeholder reporting.",
                "Performed data validation and reconciliation to improve report reliability.",
            ],
            "tools": ["SQL", "Power BI"],
            "domain": ["Product Analytics"],
        }
    ],
    "projects": [
        {
            "name": "Sales Forecast",
            "tech_stack": ["Python", "Pandas"],
            "bullets": ["Analyzed purchase behavior and sales trends."],
        }
    ],
}


def flags_for(section, bullets, name="Example Co"):
    item = {"company" if section == "experience" else "name": name, "bullets": bullets}
    return flag_unsupported_bullets({section: [item]}, MASTER_RESUME)


def test_exact_supported_bullet_is_not_flagged():
    assert flags_for("experience", ["Built SQL dashboards for recurring stakeholder reporting."]) == []


def test_paraphrased_supported_bullet_is_not_flagged():
    assert flags_for("experience", ["Created SQL dashboards for regular stakeholder reports."]) == []


def test_supported_bullet_with_canonical_metric_is_not_flagged():
    resume = {
        **MASTER_RESUME,
        "projects": [{
            "name": "Sales Forecast",
            "tech_stack": ["Python"],
            "bullets": ["Analyzed 500K+ purchase records using Python."],
        }],
    }
    tailored = {"projects": [{"name": "Sales Forecast", "bullets": ["Used Python to analyze 500K+ purchase records."]}]}

    assert flag_unsupported_bullets(tailored, resume) == []


def test_invented_metric_is_flagged():
    flags = flags_for("experience", ["Built SQL dashboards and improved efficiency by 30%."])

    assert len(flags) == 1
    assert any("unsupported metric" in reason for reason in flags[0].reasons)


def test_invented_technology_is_flagged():
    flags = flags_for("experience", ["Built Tableau dashboards for stakeholder reporting."])

    assert len(flags) == 1
    assert any("unsupported technology/tool" in reason for reason in flags[0].reasons)


def test_invented_responsibility_is_flagged():
    flags = flags_for("experience", ["Managed payroll compliance and vendor contracting."])

    assert len(flags) == 1
    assert any("not adequately supported" in reason for reason in flags[0].reasons)


def test_invented_achievement_is_flagged():
    flags = flags_for("experience", ["Won company-wide excellence award for leading the division."])

    assert len(flags) == 1
    assert any("not adequately supported" in reason for reason in flags[0].reasons)


def test_multiple_supported_facts_can_be_combined():
    flags = flags_for(
        "experience",
        ["Built SQL dashboards and performed data validation for stakeholder reporting."],
    )

    assert flags == []


def test_clearly_unsupported_bullet_is_flagged():
    flags = flags_for("experience", ["Designed aerospace propulsion systems in Java."])

    assert len(flags) == 1
    assert flags[0].section == "experience"
    assert flags[0].source_name == "Example Co"
    assert flags[0].index == 0


def test_unknown_project_is_flagged_without_deleting_content():
    tailored = {"projects": [{"name": "Invented Project", "bullets": ["Built a new platform."]}]}

    flags = flag_unsupported_bullets(tailored, MASTER_RESUME)

    assert len(flags) == 1
    assert "unknown project" in flags[0].reasons[0]
    assert tailored["projects"][0]["bullets"] == ["Built a new platform."]


def test_empty_inputs_have_no_flags():
    assert flag_unsupported_bullets({}, MASTER_RESUME) == []
    assert flag_unsupported_bullets({"experience": []}, {}) == []

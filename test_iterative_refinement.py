"""
Tests for the iterative tailoring loop in resume_generator.generate_resume
(max_iterations > 1): retries a failed attempt with feedback, and always
uses the last attempt made for the final output/decision.
"""
import pytest
from pypdf import PdfWriter

from src import resume_generator
from src.ats_scorer import ATSScore
from src.resume_generator import _attempt_has_issues, _build_feedback
from src.unsupported_claims import UnsupportedBullet


def test_attempt_has_issues_true_for_multi_page():
    assert _attempt_has_issues(2, [], ATSScore()) is True


def test_attempt_has_issues_true_for_unsupported_flags():
    flag = UnsupportedBullet(section="experience", source_name="Acme", index=0, bullet="x", reasons=["r"])
    assert _attempt_has_issues(1, [flag], ATSScore()) is True


def test_attempt_has_issues_true_for_missing_required_keywords():
    assert _attempt_has_issues(1, [], ATSScore(required_missing=2)) is True


def test_attempt_has_issues_false_when_only_preferred_keywords_missing():
    # Missing PREFERRED (not required) keywords alone must not trigger a retry.
    score = ATSScore(preferred_missing=3, required_missing=0)
    assert _attempt_has_issues(1, [], score) is False


def test_attempt_has_issues_false_for_clean_attempt():
    assert _attempt_has_issues(1, [], ATSScore()) is False


def test_build_feedback_mentions_page_overflow():
    feedback = _build_feedback(2, [], ATSScore())
    assert "one page" in feedback
    assert "2 page" in feedback


def test_build_feedback_lists_flagged_bullets_with_reasons():
    flag = UnsupportedBullet(
        section="projects",
        source_name="Widget",
        index=0,
        bullet="Reduced latency by 90%.",
        reasons=['unsupported metric "90%"'],
    )
    feedback = _build_feedback(1, [flag], ATSScore())
    assert "Widget" in feedback
    assert "Reduced latency by 90%." in feedback
    assert "unsupported metric" in feedback


def test_build_feedback_caps_flagged_bullets_shown():
    flags = [
        UnsupportedBullet(section="experience", source_name="Acme", index=i, bullet=f"Bullet {i}", reasons=["r"])
        for i in range(12)
    ]
    feedback = _build_feedback(1, flags, ATSScore())
    assert "more flagged bullet(s)" in feedback
    assert "Bullet 0" in feedback
    assert "Bullet 11" not in feedback


def test_build_feedback_lists_missing_required_keywords():
    score = ATSScore(missing_keywords=["Snowflake", "dbt"], required_missing=2)
    feedback = _build_feedback(1, [], score)
    assert "Snowflake" in feedback
    assert "dbt" in feedback


def test_build_feedback_empty_for_clean_attempt():
    assert _build_feedback(1, [], ATSScore()) == ""


def write_pdf(path, page_count):
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as file:
        writer.write(file)


def _base_patches(monkeypatch):
    monkeypatch.setattr(resume_generator, "load_master_resume", lambda path: {})
    monkeypatch.setattr(resume_generator, "extract_requirements", lambda jd: [])
    monkeypatch.setattr(resume_generator, "match_evidence", lambda reqs, master: reqs)
    monkeypatch.setattr(resume_generator, "print_analysis", lambda reqs: None)
    monkeypatch.setattr(resume_generator, "print_ats_score", lambda score: None)
    monkeypatch.setattr(resume_generator, "print_evidence_check", lambda flags, total: None)
    monkeypatch.setattr(resume_generator, "render_latex", lambda *args: None)


def test_retries_and_succeeds_on_second_attempt(tmp_path, monkeypatch):
    """
    First attempt: 2-page PDF (issue). Second attempt: 1-page PDF (fixed).
    With max_iterations=2, the retry must happen automatically, using
    feedback derived from the first attempt, and the final result must be
    the successful (1-page) second attempt.
    """
    _base_patches(monkeypatch)

    pdf_paths = [tmp_path / "attempt1.pdf", tmp_path / "attempt2.pdf"]
    write_pdf(pdf_paths[0], 2)
    write_pdf(pdf_paths[1], 1)

    calls = {"tailor": [], "compile": 0}

    def fake_tailor_resume(master, jd, requirements, feedback=None):
        calls["tailor"].append(feedback)
        return {"summary": "ok"}

    def fake_compile_pdf(*args):
        path = pdf_paths[calls["compile"]]
        calls["compile"] += 1
        return path

    monkeypatch.setattr(resume_generator, "tailor_resume", fake_tailor_resume)
    monkeypatch.setattr(resume_generator, "score_keyword_coverage", lambda tailored, reqs: ATSScore())
    monkeypatch.setattr(resume_generator, "flag_unsupported_bullets", lambda tailored, master: [])
    monkeypatch.setattr(resume_generator, "compile_pdf", fake_compile_pdf)

    result = resume_generator.generate_resume(
        "test job description",
        max_iterations=2,
    )

    # Two tailoring attempts: first with no feedback, second with feedback
    # describing the page overflow.
    assert len(calls["tailor"]) == 2
    assert calls["tailor"][0] is None
    assert calls["tailor"][1] is not None
    assert "page" in calls["tailor"][1].casefold()

    # The final result reflects the successful second attempt.
    assert result == pdf_paths[1]


def test_retries_on_unsupported_claims_and_missing_required_keywords(tmp_path, monkeypatch):
    _base_patches(monkeypatch)

    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 1)  # one page throughout -- only content issues trigger retry

    flag = UnsupportedBullet(
        section="experience",
        source_name="Acme",
        index=0,
        bullet="Led a team of 50 engineers.",
        reasons=['unsupported metric "50"'],
    )

    calls = {"tailor": [], "flags_call": 0}

    def fake_tailor_resume(master, jd, requirements, feedback=None):
        calls["tailor"].append(feedback)
        return {"summary": "ok"}

    def fake_flag_unsupported_bullets(tailored, master):
        # Only flag on the first attempt; the (simulated) retry fixes it.
        calls["flags_call"] += 1
        return [flag] if calls["flags_call"] == 1 else []

    scores = [
        ATSScore(missing_keywords=["Snowflake"], required_missing=1),
        ATSScore(),
    ]

    def fake_score_keyword_coverage(tailored, reqs):
        return scores[min(len(calls["tailor"]) - 1, len(scores) - 1)]

    monkeypatch.setattr(resume_generator, "tailor_resume", fake_tailor_resume)
    monkeypatch.setattr(resume_generator, "score_keyword_coverage", fake_score_keyword_coverage)
    monkeypatch.setattr(resume_generator, "flag_unsupported_bullets", fake_flag_unsupported_bullets)
    monkeypatch.setattr(resume_generator, "compile_pdf", lambda *args: pdf_path)

    result = resume_generator.generate_resume(
        "test job description",
        max_iterations=2,
    )

    assert len(calls["tailor"]) == 2
    feedback = calls["tailor"][1]
    assert "unsupported metric" in feedback.casefold()
    assert "snowflake" in feedback.casefold()
    assert result == pdf_path


def test_stops_after_max_iterations_even_with_unresolved_issues(tmp_path, monkeypatch):
    """
    If every attempt keeps overflowing, the loop must stop at max_iterations
    (not retry forever) and apply the normal one-page enforcement to the
    last attempt.
    """
    _base_patches(monkeypatch)

    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 2)

    calls = {"tailor": 0}

    def fake_tailor_resume(master, jd, requirements, feedback=None):
        calls["tailor"] += 1
        return {"summary": "ok"}

    monkeypatch.setattr(resume_generator, "tailor_resume", fake_tailor_resume)
    monkeypatch.setattr(resume_generator, "score_keyword_coverage", lambda tailored, reqs: ATSScore())
    monkeypatch.setattr(resume_generator, "flag_unsupported_bullets", lambda tailored, master: [])
    monkeypatch.setattr(resume_generator, "compile_pdf", lambda *args: pdf_path)

    with pytest.raises(RuntimeError, match="Generated resume exceeds one page"):
        resume_generator.generate_resume(
            "test job description",
            max_iterations=3,
        )

    # Exactly 3 attempts, no more (the loop must not run indefinitely).
    assert calls["tailor"] == 3


def test_max_iterations_one_matches_original_single_shot_behavior(tmp_path, monkeypatch):
    """
    Explicitly setting max_iterations=1 (or leaving it at the default) must
    make exactly one tailoring attempt, with no feedback kwarg -- the
    original Phase 1/2 behavior, byte-for-byte.
    """
    _base_patches(monkeypatch)

    pdf_path = tmp_path / "generated.pdf"
    write_pdf(pdf_path, 1)

    calls = {"tailor": 0}

    def fake_tailor_resume(master, jd, requirements):
        # Deliberately fixed-arity, no feedback param -- must never be
        # called with a feedback kwarg when max_iterations=1.
        calls["tailor"] += 1
        return {"summary": "ok"}

    monkeypatch.setattr(resume_generator, "tailor_resume", fake_tailor_resume)
    monkeypatch.setattr(resume_generator, "score_keyword_coverage", lambda tailored, reqs: ATSScore())
    monkeypatch.setattr(resume_generator, "flag_unsupported_bullets", lambda tailored, master: [])
    monkeypatch.setattr(resume_generator, "compile_pdf", lambda *args: pdf_path)

    result = resume_generator.generate_resume("test job description", max_iterations=1)

    assert calls["tailor"] == 1
    assert result == pdf_path

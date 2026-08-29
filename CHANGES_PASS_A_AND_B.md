# Pass A + Pass B — applied to job_apply_bot_phase2_final.zip

Full suite: 110 passed, 5 skipped, 0 failures (up from the reported 93/4,
which only held on a machine with a local `.env` already set — see fix #1).
Verified with and without a local `.env` present.

## Pass A — regression fixes

**1. `test_mistral_models.py` was silently spending real API credits on
every `pytest` run, and broke collection entirely without a local
`MISTRAL_API_KEY`.**
It was a bare top-level script (no pytest skip guard, unlike every other
manual/API script in the repo) that called `client.chat.complete()` seven
times — once per model — as an import-time side effect. Added the same
`pytest.skip(..., allow_module_level=True)` guard used by
`test_mistral.py`/`test_tailor.py`/`test_latex.py`/`test_yaml.py`. It's
still runnable directly (`python test_mistral_models.py`) when you actually
want to check model availability.

**2. `format_contact` no longer wrapped the email in a `mailto:` link.**
Restored `\href{mailto:...}{...}`. Added a dedicated regression test
(`test_format_contact_email_is_a_mailto_link`) so this can't silently
regress again, and updated the one existing test that had been written
against the broken (plain-text) output.

**3. `requirements.txt` had reverted**, losing the explicit `httpx` pin
(directly imported in `mistral_client.py`, previously only present
transitively via `mistralai`) and the `mistralai<3.0.0` upper bound.
Restored both.

**4. `.env.example` had reverted** to only documenting `MISTRAL_API_KEY`.
Restored full documentation of every env var the code actually reads
(`MISTRAL_MODEL`, `LATEX_ENGINE`, `MISTRAL_TIMEOUT_MS`,
`MISTRAL_MAX_RETRIES`, `MISTRAL_RETRY_BACKOFF_SECONDS`), and added the new
`MAX_TAILOR_ITERATIONS` (see Pass B).

**5. `main.py` had lost the `--allow-multi-page` flag** (the underlying
`strict_one_page` support in `resume_generator.py` was untouched and still
worked, just unreachable from the CLI). Restored it, and added the new
`--max-iterations` flag alongside it.

**6. Three `.backup` files were left in the tree** (`llm_tailor.py.backup`,
`latex_renderer.py.backup`, `resume_template.tex.backup`), and `.gitignore`
had no rule excluding them. Removed the files, added `*.backup` to
`.gitignore`.

**7. `format_projects` had lost its defensive guards** (no
`isinstance(project, dict)` check, no skip for a missing name or empty
bullets, no handling for an all-invalid project list). Restored all of
them, keeping the current single-description-per-project design. Added
`test_format_projects_skips_entries_without_a_name_or_bullets` and
`test_format_projects_returns_empty_string_for_no_valid_projects`.

**8. `README.md` was stale**, still describing the project as "currently
in Phase 1" with Phase 2 listed as future work, despite Phase 2 already
being fully implemented. Rewritten to describe the actual current
pipeline, features, usage (including the new `--max-iterations` flag), and
test-suite behavior.

## Pass B — iterative refinement (new feature)

Added an opt-in retry loop so the pipeline can act on its own diagnostics
instead of only reporting them.

**`src/llm_tailor.py`**: `tailor()` / `tailor_resume()` now accept an
optional `feedback: str = None` parameter. When present, it's injected into
the user prompt as a "PREVIOUS ATTEMPT FEEDBACK" section instructing the
model to address the listed issues using only master-resume facts (never to
invent new content to satisfy a piece of feedback). Building block:
`_feedback_section()`.

**`src/resume_generator.py`**: `generate_resume()` gained a
`max_iterations` parameter (default `None`, resolving to
`config.MAX_TAILOR_ITERATIONS`, itself defaulting to `1`). Per attempt, it:
1. Tailors (with feedback from the previous attempt, if any)
2. Scores ATS keyword coverage and flags unsupported claims
3. Renders and compiles to PDF, checks page count
4. Decides via `_attempt_has_issues()` whether the attempt is acceptable:
   an attempt is retried if it overflows one page, has any unsupported-claim
   flags, or is missing at least one *required* (not merely preferred) JD
   keyword.
5. If unacceptable and attempts remain, `_build_feedback()` turns the
   specific diagnostics into plain-text feedback for the next attempt.
6. The last attempt made (whether or not it was ultimately acceptable) is
   always the one rendered, and the existing one-page enforcement
   (diagnostic report + raise/warn per `strict_one_page`) is applied to it
   unchanged.

**Default behavior is unchanged.** With `max_iterations=1` (the default),
the loop runs exactly once with no feedback ever generated — byte-for-byte
identical call pattern to the pre-Pass-B code. This was verified directly:
`test_max_iterations_one_matches_original_single_shot_behavior` uses a
deliberately fixed-arity `tailor_resume` mock (no `feedback` parameter at
all) and confirms it's never called with one.

**New env var / CLI flag**: `MAX_TAILOR_ITERATIONS` (`.env`) and
`--max-iterations` (CLI, overrides the env var). Both optional; the feature
is fully opt-in.

**New tests**: `test_iterative_refinement.py` (14 tests) covering:
- The two pure decision functions (`_attempt_has_issues`, `_build_feedback`)
  in isolation, including the "preferred-only" keyword case that must
  *not* trigger a retry.
- A full retry-and-succeed scenario (2-page attempt 1 → 1-page attempt 2),
  asserting the feedback text actually reaches the second `tailor_resume`
  call and the final result is the successful attempt.
- A retry triggered by unsupported-claim flags + missing required keywords,
  asserting the feedback text names the specific flagged bullet and the
  specific missing keyword.
- Exhausting `max_iterations` without ever resolving the issue: confirms
  the loop stops at exactly the configured attempt count (no infinite
  retry) and still raises the normal one-page error on the last attempt.
- The default (`max_iterations=1`) path, confirmed identical to original
  behavior.

## Not changed

Per your instruction, no existing passing test was weakened to make new
code pass — where a test's assertion no longer matched correct behavior
(the `mailto:` case), the assertion was corrected to match the *fixed*
behavior, and a dedicated regression test was added on top so the original
bug can't return silently.

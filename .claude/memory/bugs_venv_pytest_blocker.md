---
name: Broken venv symlink prevents full pytest from executing
description: GLM external review (2026-04-26) confirmed that `pytest tests/` cannot complete because the .venv symlink resolves to a missing path on the developer laptop. Codex audit observed the same stall. Until this is fixed, every "tests pass" claim is unverifiable; LB-4 acceptance is gated on it.
type: feedback
---

Both Codex's self-audit and the GLM external review independently noted that `pytest tests/` does not run to completion on the founder's laptop. The reported root causes converged on:

1. **`.venv/bin/python` is a symlink** to a Python interpreter that no longer exists at the linked path (e.g. moved Homebrew Python, deleted system Python, broken Pyenv shim).
2. **`tests/orchestration/test_router.py::TestRouterAgainstEvaluationDataset::test_accuracy_on_dataset`** stalls — the evaluation dataset is loaded fresh on every run; without caching it can take minutes to hours, indistinguishable from a deadlock.
3. **Broken `tests/conftest.py` fixtures** that depend on a running PostgreSQL the laptop doesn't have, blocking collection.

Until these are resolved, **any claim of "tests pass" / "43/43 green" is at most a claim about the focused regression file**, not the full suite.

**Why:** External audit channels keep flagging this because LB-4 acceptance ("full pytest <15 min, all green") cannot be evidenced when the suite physically refuses to run on the canonical developer machine. It is also the reason the 4-point disagreement between Codex and Guru self-audits exists — neither one could actually run the suite, so they both extrapolated.

**How to apply:**
- LB-4 (`protocols/49_LB4_TEST_SUITE_FULL_GREEN.md`) Phase 1 acceptance MUST include: "venv recreated from scratch (`rm -rf .venv && python3.11 -m venv .venv && .venv/bin/pip install -e '.[dev]'`); `.venv/bin/python -c 'import sys; print(sys.executable)'` returns a real path; this exact command sequence committed to `evidence/<date>/venv_rebuild.log`."
- The router-eval test is `@pytest.mark.slow` and excluded from the default run (LB-4 Phase 1 fortify) — verified by the slow-test-marker pre-commit hook.
- `tests/conftest.py` fixtures gracefully `pytest.skip()` if PostgreSQL is unreachable, instead of hanging. Implementation: `try/except OperationalError` around the connection probe with a 2s timeout.
- A canonical "fresh laptop" smoke test: `bash scripts/run_test_suite.sh` from a clean clone with only `python3.11` available must finish under 15 min. Documented as the reproducibility floor.
- Until LB-4 lands these fixes, every audit-reliability check (`feedback_audit_reliability_check.md`) must explicitly say "test suite did not execute; partial-suite evidence only" rather than implying the suite passed.

**Source:** Codex `NRG_SELF_AUDIT_REPORT_2026-04-24.md` + GLM external review 2026-04-26. Promoted 2026-04-26.

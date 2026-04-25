═══════════════════════════════════════════════════════════════
TASK: LB-4 — TEST-SUITE FULL GREEN + PARALLELIZATION
AGENT: testing + devops
PRIORITY: P0 (quality gate for any release tag)
MILESTONE: M7 (CI/CD)
QUALITY BAR: meta — gate for every other constraint
RISK REGISTER: prerequisite for T-60 walk
═══════════════════════════════════════════════════════════════

FILES:
  - tests/orchestration/test_router.py — split slow tests
  - pyproject.toml or pytest.ini — markers + xdist config
  - .github/workflows/test.yml (or local pre-commit equivalent)
  - scripts/run_test_suite.sh (NEW)
  - evidence/2026-04-26/test_suite_full.xml (NEW — junit)

PROBLEM:
  pytest tests/ -v --tb=short stalls on
  TestRouterAgainstEvaluationDataset; no pytest-xdist parallelisation. We
  cannot prove "full green" before launch without a sub-15-minute gate the
  operator can run on a laptop.

ACTION:
  Phase 1 — FORTIFY: mark heavy router-eval test @pytest.mark.slow;
    install pytest-xdist; default `pytest -n auto -m "not slow"` for
    sub-15-min runs.
  Phase 2 — ELEVATE: split slow tests into a separate nightly job;
    flake-detection via pytest-rerunfailures; emit junit XML to evidence/.
  Phase 3 — IMMORTALIZE: pre-commit hook blocks any new test exceeding 30s
    without @pytest.mark.slow.

SKILLS TO USE:
  - /testing-strategy
  - /python-backend
  - /code-review-and-quality

ACCEPTANCE CRITERIA:
  - [ ] bash scripts/run_test_suite.sh finishes <15 min, all green,
        on a developer laptop. Evidence: junit XML committed.
  - [ ] Slow suite finishes <30 min nightly, all green.
  - [ ] Pre-commit hook blocks new tests >30s without slow marker.

BEFORE COMMIT:
  - /pre-commit + /code-review-and-quality

GURU ASSIGNMENT NOTE:
  Operations team must be able to run the full gate in <15 min before any
  release. A stalling suite = no production launch.

AGENT INSTRUCTIONS (verbatim):
  - Standard agent reads (production_only, AGENTS, shishya, QUALITY_BAR).
  - Read every SKILL.md listed.
  - Fortify → Elevate → Immortalize.
  - /pre-commit before commit.

DEPENDS ON: none (parallel-safe to LB-1/2/3/5)
BLOCKS: production launch
═══════════════════════════════════════════════════════════════

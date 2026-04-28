---
name: pr-review-toolkit
description: Comprehensive PR review using parallel specialized agents — comments, tests, errors, types, quality, simplification. Run before any merge. Produces structured review with APPROVE / REQUEST CHANGES verdict.
model-agnostic: true
---

# PR Review Toolkit

Six review agents. Run in parallel by default. Each catches different failure classes.

## Usage

```bash
# Get the diff
git diff main...HEAD --stat
git diff main...HEAD --name-only

# Check if PR exists
gh pr view 2>/dev/null
```

---

## Step 1 — Determine Scope

From `git diff --name-only`, determine which agents apply:

| Condition | Agent |
|---|---|
| Always | `code-reviewer` (general quality, project conventions) |
| Test files changed | `pr-test-analyzer` (coverage, behavioral gaps) |
| Comments/docs added | `comment-analyzer` (accuracy vs code, comment rot) |
| Error handling changed | `silent-failure-hunter` (catch blocks, logging gaps) |
| Types added/modified | `type-design-analyzer` (invariants, encapsulation) |
| After all others pass | `code-simplifier` (DRY, over-engineering, dead code) |

---

## Step 2 — Launch Agents

**Parallel (default):** Launch all applicable agents simultaneously.

**Sequential (when issues are expected):** Run one at a time, easier to act on each report.

Each agent receives:
- The git diff
- The files changed
- The PR description (if available)

---

## Agent Responsibilities

### comment-analyzer
- Verifies comment accuracy vs actual code behavior
- Finds comment rot (comments describing old behavior)
- Checks documentation completeness on public interfaces
- **Flag:** TODO/FIXME/HACK left in committed code

### pr-test-analyzer
- Reviews behavioral test coverage (not just line coverage)
- Identifies critical gaps — new branches without tests
- Evaluates test quality: tests that can't fail are theater
- **NRG rule:** No DB mocks. New API endpoints need tier isolation test.

### silent-failure-hunter
- Finds exceptions caught but not logged
- Finds errors that produce 500s to end users
- Checks audit log on exceptions in API handlers
- **NRG rule:** Every API handler must catch + log + return user-friendly message

### type-design-analyzer
- Analyzes type encapsulation and invariants
- Flags `Any` types that could be narrowed
- Flags Optional fields accessed without None check
- **NRG rule:** Pydantic models preferred over raw dicts for API shapes

### code-reviewer
- Checks project conventions and patterns
- Detects bugs and logic errors
- Reviews general code quality
- **NRG rule:** Verify response_filter.apply() called on all DB-touching endpoints

### code-simplifier
- Identifies duplication (3+ identical lines in different places)
- Flags functions >50 lines without clear decomposition
- Flags magic numbers/strings without named constants
- Flags over-engineered solutions for simple problems

---

## Step 3 — Aggregate Results

```
# PR Review Summary

## Critical Issues (must fix before merge)
- [agent]: Issue description [file:line]

## Important Issues (should fix)
- [agent]: Issue description [file:line]

## Suggestions (optional improvements)
- [agent]: Suggestion [file:line]

## Strengths
- What's well done in this PR
```

---

## Final Verdict

```
PR REVIEW: [branch-name] → main
Date: [date]

comment-analyzer:    PASS / FAIL: [issue]
pr-test-analyzer:    PASS / FAIL: [issue]
silent-failure-hunter: PASS / FAIL: [issue]
type-design-analyzer: PASS / FAIL: [issue]
code-reviewer:       PASS / FAIL: [issue]
code-simplifier:     PASS / FAIL: [issue]

VERDICT: APPROVE / REQUEST CHANGES
Blockers: [must fix before merge]
Suggestions: [optional]
```

Merge only on APPROVE with zero blockers.

---

## For NRG — Additional Checks

Before any verdict, verify:
- [ ] `response_filter.apply()` called on all endpoints returning data
- [ ] All DB queries in API handlers emit audit events
- [ ] No raw LLM SQL executed without `sql_validator.validate()`
- [ ] No PII in LLM payloads
- [ ] `forbidden_vocab_check.sh` passes on all `.md` files

---

## Anti-Patterns

- Running only `code-reviewer` and skipping specialized agents
- Marking APPROVE when critical issues exist "because they're minor"
- Running review after creating the PR instead of before
- Skipping `pr-test-analyzer` when "tests weren't the focus"

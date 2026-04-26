---
name: Audit reliability — disagreeing self-audits are themselves a failure signal
description: When two internal self-audits produced on the same day disagree by ≥3 points on a 1-10 readiness score (e.g. Codex 4/10, Guru 8/10), the disagreement itself is a P0 incident. The team does not know the real state of the system. Reconcile before any external session.
type: feedback
---

NRG produced two same-day self-audits (Codex `NRG_SELF_AUDIT_REPORT_2026-04-24.md` and Guru's V4 wrap report) whose readiness scores disagreed by ~4 points on a 1-10 scale. Multiple external reviewers (GLM, Kimi, MiniMax) converged on the same observation: **the disagreement is itself the bug**. It signals one or more of:

1. The auditors used different evidence sets (one read live evidence, the other read only the BACKLOG claim).
2. Neither actually executed the full test suite — both reported partial-suite results or extrapolated from the focused regression.
3. The Quality Bar scorecard was interpreted differently (e.g. "5/6 PASS" vs "5/5" vs "C4 SKIP counts as PASS").
4. The team has no single source of truth for "is this system OK right now?" and is reasoning from artifacts of varying freshness.

Whichever it is, **operators do not know the true state of the system**. That is a higher-severity finding than any individual gap, because it means every subsequent decision is taken on hallucinated ground truth.

**Why:** External audits flagged this as a "kill-shot" finding because a ministry official asks "is the system ready?" and gets a different answer depending on which engineer they ask. There is no recovery from "we don't know" in a credibility-driven evaluation.

**How to apply:**
- Any new self-audit MUST cite the exact `git rev-parse HEAD` it was generated against and the timestamp of the latest `scripts/quality_bar_scorecard.py` JSON it consumed. No re-running the score during the audit.
- If two self-audits within the same week disagree by ≥3 points on overall readiness, that triggers a **reconciliation protocol** (NEW): pause all sprint work, both audit authors meet, identify exact line items where they diverge, produce a combined audit that explicitly resolves each divergence with evidence. Commit the reconciliation under `evidence/<date>/audit_reconciliation_<rev>.md`.
- The Verdict Template in `.claude/QUALITY_BAR.md` is the authoritative format. Free-form scoring outside it is rejected — including by Guru responses.
- The Quality Bar scorecard JSON (`scripts/quality_bar_scorecard.json`) is the single source of truth for "OK right now?". Any audit citing a different score must explain why.
- Do not present the system to an external audience until the latest two self-audits agree to within ±1 point on overall readiness.

**Source:** Pattern observed across GLM, Kimi/Moonshot, and MiniMax external reviews 2026-04-26. Promoted 2026-04-26.

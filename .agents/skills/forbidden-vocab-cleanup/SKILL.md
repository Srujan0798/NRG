---
name: forbidden-vocab-cleanup
description: Purge production-forbidden vocabulary from external-facing NRG documents, scripts, runbooks, and release artifacts before review or commit.
---

# Forbidden Vocabulary Cleanup

Use this skill before any external-facing NRG artifact is committed, shared, tagged, or handed over.

## Required Reads

1. `.claude/rules/production_only.md`
2. `scripts/forbidden_vocab_check.sh`
3. The artifact being cleaned

## Cleanup Workflow

1. Rename files and symbols first:
   - `seed_demo_data.py` -> `seed_production_data.py`
   - `prewarm_demo_cache.py` -> `prewarm_acceptance_cache.py`
   - `NRG_50LAKH_DELIVERY_REPORT_*` -> `NRG_PRODUCTION_READINESS_REPORT_*`
2. Replace forbidden framing:
   - `demo-ready` -> `production-ready`
   - `Demo Script` -> `Launch Script`
   - `Demo Data` -> `Production Seed Data`
   - `demo verification` -> `acceptance verification`
   - `pitch deck` -> `capability brief` or remove the phrase
   - `MVP` -> `v1.0`
   - `prototype` -> `production module`
3. Scan all references:
   - `rg -n "demo|demo-ready|pitch deck|MVP|prototype|seed_demo_data|prewarm_demo_cache|NRG_50LAKH_DELIVERY_REPORT" .`
4. Run the gate:
   - `bash scripts/forbidden_vocab_check.sh --all`
5. If the gate fails, rewrite the artifact. Do not allowlist active production files.

## Acceptance Checklist

- Root `.md` reports are scanned.
- Active scripts and runbooks contain no forbidden vocabulary.
- Historical/spec files may mention forbidden words only when they are intentionally allowlisted by `scripts/forbidden_vocab_check.sh`.
- `BACKLOG.md` references current production artifact names only.
- Final report includes the exact forbidden-vocab command and exit status.

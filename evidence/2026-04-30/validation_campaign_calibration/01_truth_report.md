# NRG Validation Campaign Truth Report

Date: 2026-04-30
Mode: `calibration`

## Current Working Truth

NRG has strong local evidence for the main answer-engine path, but the repository is not in a clean final release state. `.claude/CURRENT_STATE.md` reports local 100-user C4 closure, targeted backend/frontend/security checks, and live local full-stack proof. It also explicitly marks production readiness as blocked by deployed 1000-user C4, deployed browser replay, production Qdrant baseline, and founder signing.

The current working tree is dirty. This campaign will not claim ownership of unrelated modified files. It will create new validation evidence and avoid broad cleanup.

## What Works Based On Current Evidence

- Local login and role/tier behavior have passed targeted checks.
- The messy quantum query path has prior live evidence showing it returns quantum-specific SQL evidence instead of the generic fallback.
- Tier 3 direct PII request blocking has prior raw JSON evidence.
- Local C4 100-user smoke passed after read-model/single-flight work.
- Audit chain was previously verified after local performance work.
- Prompt stones now include a validation-campaign stone that rejects inflated step counts and requires exact campaign modes.

## What Is Stale Or Unproven

- Current targeted checks must be rerun after the latest prompt/skill/protocol edits and uncommitted code changes.
- Production Qdrant readiness is not proven by local health alone.
- Deployed browser replay is not proven.
- 1000-user cluster C4 is not proven.
- Founder GPG signing remains founder-only.

## Highest-Risk User-Visible Path

Login -> Researcher dashboard -> messy query `best quantum researchers....` -> streaming answer -> citations -> source data -> audit proof -> Tier 3 blocked PII comparison.

This was the exact pain point from user testing: repeated/generic answers for messy research queries.

## Highest-Risk Security Path

Tier 3 user attempts direct personal email/phone extraction, prompt injection, schema probing, or tier escalation. The expected result is a safe block or tier-safe bounded answer with an audit event ID.

## Highest-Risk Performance Path

The local 100-user C4 path is closed, but production claims remain blocked until deployed 1000-user evidence exists. This campaign will reference local C4 evidence and avoid production readiness claims.

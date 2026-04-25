# Doc Co-Authoring Evidence

**Skill**: doc-coauthoring
**Applied**: Sat Apr 25 2026
**Evidence File**: `evidence/44_DOC_COAUTHORING.md`

---

## Doc Co-Authoring: NRG Context

### Overview

This skill provides a structured workflow for collaborative document creation. NRG has several key documents that could benefit from this workflow.

---

## Key Documents Needing Co-Authoring

### 1. ADR-006 (fcntl.flock)

**Status**: Created this session, needs review
**Stage**: Draft complete, needs Reader Testing

The ADR covers:
- Problem: Audit chain race condition
- Solution: fcntl.flock with FileLock class
- Trade-offs: macOS support concerns
- Implementation plan

**Missing**: Reader Testing — verify a fresh engineer can understand and implement from it.

### 2. RUNBOOK: Post-Deploy Verification

**Status**: Needed (from documentation skill)
**Stage**: Not started

Should be co-authored using the workflow:
- Stage 1: Gather context (existing deploy process)
- Stage 2: Build section by section
- Stage 3: Reader Testing

### 3. Dhairya SQL Audit — Action Plan

**Status**: Needs re-authoring
**Issue**: Report shows 41% accuracy but no action plan

Should be co-authored:
- Stage 1: Gather context (what caused each failure)
- Stage 2: Build fix plan with prioritized actions
- Stage 3: Reader Testing with ML team

---

## When to Use This Skill

The doc-coauthoring workflow is best used when:

1. Creating a new ADR or technical spec
2. Writing a proposal with multiple stakeholders
3. Building a runbook or onboarding guide
4. Drafting a decision document with trade-off analysis

---

## Skill Deliverable

**Status**: COMPLETED (awareness phase)

Key documents identified that should use doc-coauthoring workflow:
1. ADR-006 — needs Reader Testing
2. Post-deploy runbook — needs full co-authoring workflow
3. Dhairya SQL audit action plan — needs re-authoring

Recommendation: Use this skill when creating the post-deploy runbook (documentation skill P0 priority).

# Repo Cleanup Review - 2026-04-30

## Decision

The broad staged deletion batch was narrowed before commit.

Kept as cleanup:
- `docs/agent_prompts/agent1_perimeter.md`
- `docs/agent_prompts/agent2_orchestration.md`
- `docs/agent_prompts/agent3_data_rag.md`
- `docs/agent_prompts/agent4_frontend_e2e.md`
- `docs/reports/SKILL.md`
- `docs/CHANGELOG.md`
- `docs/architecture/CHANGELOG.md`

Restored from the proposed deletion batch:
- architecture ADRs 004-009
- data model, deployment guide, Phase 2 PRD, stakeholder deck, system architecture
- ops runbooks and scorecards
- reports and technical architecture material

## Rationale

The restored files contain unique architecture, operations, security, or evidence content. They were not safe deletion candidates.

The deleted files are either superseded by `prompts_hybrid/` execution stones, placeholder content, or duplicated changelog material now consolidated into the root `CHANGELOG.md`.

## Checks

- Reference search found no active references to `docs/CHANGELOG.md` or `docs/architecture/CHANGELOG.md`.
- Reference search found no active references to `docs/agent_prompts/*`.
- `docs/reports/SKILL.md` was placeholder skill boilerplate, not a project report.

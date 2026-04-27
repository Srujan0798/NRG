---
name: sprint-planning
description: Plan a sprint — scope work, estimate capacity, set goals, and draft a sprint plan. Use when kicking off a new sprint, sizing a backlog against team availability (accounting for PTO and meetings), deciding what's P0 vs. stretch, or handling carryover from the last sprint.
---

# /sprint-planning

Plan a sprint — scope work, estimate capacity, set goals, and draft a sprint plan.

## Usage

```
/sprint-planning <sprint goals or backlog items>
```

## When to Use

- Kicking off a new sprint
- Sizing a backlog against team availability
- Deciding what's P0 vs. stretch
- Handling carryover from the last sprint

## Workflow

1. **Calculate capacity** — Team size × days minus PTO, holidays, meetings
2. **List backlog items** — Prioritized user stories/tasks
3. **Estimate effort** — Story points or time estimates
4. **Commit to scope** — What fits in capacity (P0), what doesn't (stretch)
5. **Define sprint goal** — One-sentence objective
6. **Identify risks** — Dependencies, blockers, unknowns

## Output Format

```markdown
# Sprint [N] Plan

## Sprint Goal
[One sentence]

## Capacity
- Team: [N] people
- Available days: [N]
- Effective capacity: [N] story points

## Committed Work (P0)
| Item | Assignee | Points | Status |
|------|----------|--------|--------|
| [Item] | [Name] | [N] | Ready |

## Stretch Goals
| Item | Points |
|------|--------|
| [Item] | [N] |

## Risks
- [Risk] → [Mitigation]
```

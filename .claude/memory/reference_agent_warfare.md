---
name: Agent Warfare System
description: Full autonomous agent workflow with 13 skills, self-evolution loop, and role-based command structure
type: reference
---

The NRG project uses a comprehensive agent orchestration system documented in `.claude/AGENT_WARFARE.md`.

Key components:
- **13 skills** as slash commands (test-suite, code-review, security-audit, pre-commit, post-deploy, self-evolve, architect, sprint-plan, bug-hunt, performance, docs-sync, audit-check, deploy-local)
- **4-phase loop**: PLAN → EXECUTE → AUDIT → EVOLVE
- **Role hierarchy**: Architect (human) → CTO/Mentor/Guardian agents → Execution agents
- **Self-evolution**: After each sprint, Guardian agent updates rules, memory, and skills based on what went wrong
- **Pre-commit gate**: Every commit must pass syntax, imports, tests, and secret scan

**How to apply:** When starting a new sprint, use `/sprint-plan`. When agents finish, use `/code-review` + `/security-audit`. End sprint with `/self-evolve`.

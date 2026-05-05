# Remote Workflow And Deployment Gate Cleanup

Date: 2026-05-05

## Scope

Two untracked draft documents appeared during final verification. They were
normalized instead of committed as-is:

- `.claude/REMOTE_WORKFLOW.md` now references existing setup, verification,
  Docker, docs-link, and frontend/backend test commands.
- `prompts_hybrid/09_deployment_gate_stone.md` replaces the rough deployment
  prompt with a production-boundary gate that separates local proof from
  deployed evidence and explicit `BLOCKED` rows.
- `prompts_hybrid/00_INDEX.md` now includes the deployment gate in the prompt
  selection map.

## Boundary

This cleanup does not unblock external gates. Deployed frontend/API URLs,
production API/Qdrant targets, cluster context, remote-history/security
coordination, remote CI, and founder signing remain external blockers.

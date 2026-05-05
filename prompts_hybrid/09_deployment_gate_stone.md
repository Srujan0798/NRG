# NRG Deployment Gate Stone

Use this for deployment, release, handover, performance, or readiness work when
the difference between local proof and deployed proof matters.

## Goal

Make the deployment boundary explicit. A local run can close local engineering
work, but deployed readiness requires a reachable target environment, current
commit SHA, smoke checks, and saved evidence.

## Read First

- `.claude/CURRENT_STATE.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `prompts_hybrid/07_show_readiness_handover_stone.md`
- `scripts/deployment_gate.py`
- `scripts/run_final_external_gates.py`
- `docs/handover/FINAL_CHECKLIST.md`

## Gate Rules

1. Do not use local browser, local API, or local Docker evidence to support a
   deployed-production claim.
2. If no target URL, cluster context, production API, or production vector store
   is available, mark that row `BLOCKED` and record exactly what is missing.
3. If a target exists, record the target URL, commit SHA, deployment command,
   health output, browser proof, rollback command, and any failed checks.
4. Do not force-push or rewrite remote history unless the founder has approved
   the remote-history and credential-rotation plan.
5. Do not claim final readiness while founder signing, remote CI, deployed C4,
   production vector health, or live UAT evidence is missing.

## Required Workflow

1. Capture local state:

   ```bash
   git status --short
   git log -1 --oneline
   git rev-list --left-right --count main...nrg/main
   ```

2. Run local preflight checks relevant to the change:

   ```bash
   bash scripts/forbidden_vocab_check.sh --all
   .venv/bin/python scripts/check_docs_links.py
   .venv/bin/python scripts/deployment_gate.py --help
   ```

3. If a deployment target is available, deploy through an existing automation
   path:

   ```bash
   bash scripts/deploy.sh
   # or
   .venv/bin/python scripts/deploy.py --help
   ```

4. Verify target health with the deployed URL, not localhost:

   ```bash
   curl -fsS "$NRG_API_URL/health"
   curl -fsS "$NRG_API_URL/health/db"
   curl -fsS "$NRG_API_URL/health/qdrant"
   ```

5. For C4 or final external gates, run only when the required target context is
   present:

   ```bash
   KUBECONFIG=/path/to/sovereign-cluster \
     .venv/bin/python scripts/run_final_external_gates.py --run-cluster-load
   ```

6. If the target context is absent, create evidence that says `BLOCKED`, names
   the missing inputs, and avoids readiness language.

## Evidence Standard

Save proof under `evidence/YYYY-MM-DD/<deployment_task>/`:

- `git_head.log`
- `git_status.log`
- `deployment_command.log`
- `health_api.json`
- `health_db.json`
- `health_qdrant.json`
- `browser_screenshot.png` or Playwright trace when available
- `rollback.md`
- `BLOCKERS.md` when any gate cannot run

## Output Required

Return:

- `PASS`, `FAIL`, `BLOCKED`, or `UNKNOWN` for each gate.
- Files changed.
- Commands run.
- Evidence paths.
- Remaining blockers.
- Commit SHA if committed.

# NRG Remote Workflow

Use this when moving NRG work to a new laptop, VM, or cloud workspace. This
document covers reproducible setup and local verification only. It does not
unblock deployed-production gates by itself.

## One-Time Setup

```bash
git clone https://github.com/Srujan0798/NRG.git NRG
cd NRG
bash scripts/nrg-remote-setup.sh
```

Optional local services:

```bash
docker compose -f docker-compose.yml up -d postgres qdrant redis
```

Local compose helper:

```bash
bash scripts/deploy.sh
```

## Baseline Verification

Run these before claiming the new workspace is usable:

```bash
git status --short
bash scripts/check_workflow_links.sh
.venv/bin/python scripts/check_docs_links.py
bash scripts/forbidden_vocab_check.sh --all
.venv/bin/python -m pytest tests/orchestration/ tests/skills/ -q --tb=short --no-cov -x
cd frontend && npm run build && npm test -- --runInBand
```

When using Docker locally, also verify:

```bash
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:8000/health/db
curl -fsS http://localhost:8000/health/qdrant
```

Localhost proof supports local status only. Deployed claims require the target
frontend/API URLs and target health evidence.

## Daily Workflow

```bash
git status --short
git fetch nrg
git rev-list --left-right --count main...nrg/main
.venv/bin/python .claude/scripts/nrg-verify-workflow.py
```

If `main` and `nrg/main` have diverged, do not run a normal push as a closure
step. Coordinate the remote-history/security plan first.

After edits:

```bash
git diff --check
bash scripts/forbidden_vocab_check.sh --all
.venv/bin/python scripts/check_docs_links.py
```

Then run the smallest test slice that proves the change. For broad frontend or
orchestration work, use the baseline verification commands above.

## Deployment Boundary

Deployment or final-readiness work needs:

- reachable frontend URL
- reachable API URL
- target commit SHA
- health output from the deployed API
- browser proof from the deployed frontend
- production Qdrant/vector health when retrieval is in scope
- cluster context for C4 replay when C4 is in scope
- founder signing for signed release evidence

If those inputs are unavailable, record `BLOCKED` evidence and continue only on
local code or documentation work.

External gate runner:

```bash
KUBECONFIG=/path/to/sovereign-cluster \
  .venv/bin/python scripts/run_final_external_gates.py --run-cluster-load
```

## Evidence Storage

| Evidence size | Storage | Path |
|---|---|---|
| less than 100 KB | Git | `evidence/YYYY-MM-DD/` |
| 100 KB to 10 MB | Git LFS or object-store link | `evidence/YYYY-MM-DD/S3_LINKS.md` |
| more than 10 MB | object store only | link from `evidence/YYYY-MM-DD/S3_LINKS.md` |

Do not commit secrets, database dumps, raw private datasets, videos, or large
exports.

## Troubleshooting

| Problem | Fix |
|---|---|
| Python import errors after clone | Run `bash scripts/nrg-remote-setup.sh` |
| Frontend packages missing | Run `cd frontend && npm ci` |
| Qdrant not starting | Check Docker Desktop or Colima, then rerun compose |
| Port 8000 already in use | Stop the existing API process before `scripts/deploy.sh` |
| Broken local doc links | Run `.venv/bin/python scripts/check_docs_links.py` |
| Workflow link drift | Run `bash scripts/check_workflow_links.sh` |

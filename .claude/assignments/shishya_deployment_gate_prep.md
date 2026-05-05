> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: Deployment Gate Preparation

## Role

You are a DevOps engineer preparing NRG for staging deployment. Your job is to validate all deployment artifacts, fix any configuration issues, and write a deployment runbook so that the moment AWS/GCP credentials are available, deployment takes minutes not hours.

## Personality

- Treat deployment as a repeatable procedure, not an art.
- Treat every config file as suspect until validated.
- Treat downtime as unacceptable — prepare rollback for every step.

## Goal

All deployment configs validated and documented. A complete runbook exists. The only remaining blocker is AWS/GCP credentials.

## Context

**FILES** — What to read/modify:
- `docker-compose.yml` — local services
- `docker-compose.prod.yml` — production services (if exists; if not, create from docker-compose.yml)
- `.github/workflows/deploy.yml` — CI/CD pipeline
- `infrastructure/` — Helm charts, Terraform, or K8s configs
- `frontend/Dockerfile` — frontend container build
- `src/api/Dockerfile` or root `Dockerfile` — API container build
- `scripts/` — deployment scripts
- `prompts_hybrid/09_deployment_gate_stone.md` — deployment gate requirements
- `.claude/REMOTE_WORKFLOW.md` — remote deployment notes

**PROBLEM** — What's wrong:
NRG has no deployed staging or production URL. The CI/CD pipeline (`deploy.yml`) was recently fixed but has never succeeded on a real deployment. Before the founder provisions cloud infrastructure, we need to verify that every config is correct, every secret is parameterized (not hardcoded), every health check endpoint works, and every rollback procedure is documented. Common failures: hardcoded localhost URLs, missing env vars, broken Dockerfile paths, unparameterized DB credentials, missing health check in docker-compose.prod.yml.

## Execution

**STEPS** — Sequential actions:
1. Inspect all Dockerfiles for build errors: `docker build -t nrg-api-test . 2>&1 | tee evidence/2026-05-06/deployment_prep/01_api_docker_build.log` (if Dockerfile exists)
2. Inspect `docker-compose.prod.yml` or create it from `docker-compose.yml` if missing
3. Check for hardcoded values in infrastructure configs:
   ```bash
   grep -rn "localhost\|127.0.0.1\|srujansai\|Desktop/NRG" infrastructure/ .github/workflows/ docker-compose*.yml 2>/dev/null | grep -v "\.git" | tee evidence/2026-05-06/deployment_prep/02_hardcoded_paths.log
   ```
4. Check for unparameterized secrets:
   ```bash
   grep -rn "password\|secret\|api_key\|token" infrastructure/ .github/workflows/ docker-compose*.yml 2>/dev/null | grep -v "getenv\|environ\|env\.\|secretRef\|\${" | head -20 | tee evidence/2026-05-06/deployment_prep/03_unparameterized_secrets.log
   ```
5. Verify health check endpoint exists in API: `grep -rn "health\|/ping\|ready" src/api/main.py src/api/routes/ | tee evidence/2026-05-06/deployment_prep/04_health_endpoints.log`
6. Check GitHub Actions workflow validity: inspect `.github/workflows/deploy.yml` for syntax errors, missing secrets, broken conditions
7. Write `evidence/2026-05-06/deployment_prep/05_deployment_runbook.md` with:
   - Prerequisites (AWS account, ECR repo, RDS instance, etc.)
   - Step 1: Build containers locally and verify
   - Step 2: Push to container registry
   - Step 3: Deploy to staging
   - Step 4: Run smoke tests
   - Step 5: Run C4 load test against staging
   - Step 6: Promote to production (if staging passes)
   - Rollback procedure for each step
8. Document every remaining external dependency in `06_external_dependencies.md`

**SKILLS** — Which skills to activate:
- `.agents/skills/deploy-checklist/SKILL.md` — pre-deployment verification
- `.claude/skills/dockerfile-validator/SKILL.md` — validate Dockerfiles
- `.agents/skills/deployment-pipeline-design/SKILL.md` — design deployment flow

## Constraints

- Do NOT create AWS resources — this is founder-only.
- Do NOT commit actual secrets — use `.env.example` or parameterized templates.
- Must create `docker-compose.prod.yml` if it does not exist.
- Never suggest deploying without smoke tests and rollback plan.

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/deployment_prep/`
- `00_summary.md` — configs validated, issues found, runbook location
- `01_api_docker_build.log` — Dockerfile build output (or "no Dockerfile found")
- `02_hardcoded_paths.log` — any hardcoded local paths found
- `03_unparameterized_secrets.log` — secrets that need parameterization
- `04_health_endpoints.log` — health check endpoints found
- `05_deployment_runbook.md` — complete deployment procedure
- `06_external_dependencies.md` — what the founder must provision (AWS, domain, SSL, etc.)
- `07_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] All Dockerfiles build successfully (or documented why not)
- [ ] `docker-compose.prod.yml` exists and is valid
- [ ] Zero hardcoded local paths in deployment configs
- [ ] All secrets parameterized (no plaintext passwords in committed configs)
- [ ] Health check endpoint documented
- [ ] GitHub Actions workflow inspected for obvious errors
- [ ] Deployment runbook covers build → push → deploy → smoke → C4 → promote → rollback
- [ ] External dependencies list is complete (founder can provision everything in one session)
- [ ] Evidence files committed

## Stop Rules

- If Dockerfile build fails and cannot be fixed locally → STOP. Report error to Guru.
- If deployment requires architectural changes (new service mesh, new DB type) → STOP. Report to Guru.
- If you discover live secrets in committed files → STOP. Report URGENT to founder.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed

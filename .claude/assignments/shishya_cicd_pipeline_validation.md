> **Before You Start:** Read `.agents/AGENTS.md` → then read every SKILL.md listed below → then begin.
>
> **After Completing:** Run `/pre-commit` → then report back per `.agents/AGENTS.md` §Report Back.

# ASSIGNMENT: CI/CD Pipeline Validation

## Role

You are a DevOps engineer auditing the NRG continuous integration and deployment pipeline. Your job is to validate every GitHub Actions workflow, fix syntax errors, identify missing secrets, and produce a CI/CD health report so the pipeline is ready to deploy the moment staging infrastructure exists.

## Personality

- Treat CI/CD as production code — every line must be correct.
- Treat secrets as invisible — document what is needed, never expose values.
- Treat failed workflows as data — capture exact error messages and line numbers.

## Goal

All GitHub Actions workflows are syntactically valid, correctly configured, and documented with a complete secrets inventory and deployment checklist.

## Context

**FILES** — What to read/modify:
- `.github/workflows/deploy.yml` — main deployment workflow
- `.github/workflows/test.yml` or `ci.yml` — test workflow (if exists)
- `.github/workflows/` — any other workflow files
- `scripts/` — scripts called by workflows
- `docker-compose.yml` — services referenced by deployment
- `docker-compose.prod.yml` — production services (if exists)
- `.claude/REMOTE_WORKFLOW.md` — remote deployment notes
- `prompts_hybrid/09_deployment_gate_stone.md` — deployment gate requirements

**PROBLEM** — What's wrong:
The CI/CD pipeline (`deploy.yml`) was recently fixed for pytest e2e isolation, deploy-production condition, and Semgrep continue-on-error, but it has never succeeded on a real deployment. Before the founder provisions cloud infrastructure, we need to verify: (1) workflow syntax is valid, (2) all referenced secrets are documented, (3) all script paths exist, (4) Docker build steps are correct, (5) rollback conditions are present, (6) no hardcoded values leak through.

## Execution

**STEPS** — Sequential actions:
1. List all workflows: `ls -la .github/workflows/ | tee evidence/2026-05-06/cicd_validation/01_workflow_list.log`
2. Validate YAML syntax for each workflow:
   ```bash
   for f in .github/workflows/*.yml; do
     .venv/bin/python -c "import yaml; yaml.safe_load(open('$f'))" 2>&1 && echo "OK: $f" || echo "FAIL: $f"
   done | tee evidence/2026-05-06/cicd_validation/02_yaml_syntax.log
   ```
3. Check for missing secrets: grep all `secrets.` references and document which ones are required:
   ```bash
   grep -rn "secrets\." .github/workflows/ | sort | uniq | tee evidence/2026-05-06/cicd_validation/03_secrets_references.log
   ```
4. Check for hardcoded values in workflows:
   ```bash
   grep -rn "srujansai\|Desktop/NRG\|localhost\|127.0.0.1" .github/workflows/ | tee evidence/2026-05-06/cicd_validation/04_hardcoded_values.log
   ```
5. Verify all script paths referenced in workflows exist:
   ```bash
   grep -roh "scripts/[a-zA-Z0-9_./-]*" .github/workflows/ | sort | uniq | while read path; do
     if [ -f "$path" ]; then echo "EXISTS: $path"; else echo "MISSING: $path"; fi
   done | tee evidence/2026-05-06/cicd_validation/05_script_paths.log
   ```
6. Check Dockerfile references in workflows:
   ```bash
   grep -rn "docker build\|Dockerfile" .github/workflows/ | tee evidence/2026-05-06/cicd_validation/06_docker_references.log
   ```
7. Inspect deploy.yml for rollback conditions:
   ```bash
   grep -n "rollback\|revert\|undo\|failure" .github/workflows/deploy.yml | tee evidence/2026-05-06/cicd_validation/07_rollback_checks.log
   ```
8. Write `evidence/2026-05-06/cicd_validation/08_secrets_inventory.md` — table of every secret needed:
   | Secret Name | Used In | Purpose | Status |
   |-------------|---------|---------|--------|
   | `AWS_ACCESS_KEY_ID` | deploy.yml | ECR push | MISSING / PRESENT |
   | etc. |
9. Write `evidence/2026-05-06/cicd_validation/09_ci_cd_health_report.md` with:
   - Workflow inventory
   - YAML syntax status per workflow
   - Missing secrets list
   - Missing script paths
   - Rollback coverage assessment
   - Recommendations

**SKILLS** — Which skills to activate:
- `.agents/skills/deploy-checklist/SKILL.md` — pre-deployment verification
- `.claude/skills/dockerfile-validator/SKILL.md` — validate container build steps
- `.agents/skills/deployment-pipeline-design/SKILL.md` — audit pipeline design

## Constraints

- Do NOT create GitHub secrets — document what is needed, founder will create them.
- Do NOT modify workflow files unless there is a clear syntax error.
- Must flag any workflow that references non-existent scripts or Dockerfiles.
- Never suggest weakening security (e.g., `continue-on-error` for security scans should be flagged, not encouraged).

## Output

**EVIDENCE** — What to produce:
`evidence/2026-05-06/cicd_validation/`
- `00_summary.md` — workflows checked, issues found, secrets missing, report location
- `01_workflow_list.log` — all workflow files
- `02_yaml_syntax.log` — YAML validation results
- `03_secrets_references.log` — all secrets referenced
- `04_hardcoded_values.log` — any hardcoded paths or values
- `05_script_paths.log` — existence check for referenced scripts
- `06_docker_references.log` — Dockerfile references
- `07_rollback_checks.log` — rollback conditions found
- `08_secrets_inventory.md` — complete secrets table
- `09_ci_cd_health_report.md` — full health report
- `10_blockers.md` — what remains blocked

**DONE WHEN** — Acceptance criteria:
- [ ] All workflow YAML files pass syntax validation
- [ ] Every `secrets.` reference is documented in the inventory
- [ ] Every script path referenced in workflows exists (or documented as missing)
- [ ] No hardcoded local paths in workflows
- [ ] Dockerfile references are valid
- [ ] Rollback conditions documented (or explicitly missing)
- [ ] Health report includes recommendations for founder
- [ ] Evidence files committed

## Stop Rules

- If a workflow has critical syntax errors that cannot be fixed locally → STOP. Report to Guru.
- If you discover live secrets committed in workflow files → STOP. Report URGENT to founder.
- If workflow references external actions that are deprecated or unmaintained → STOP. Flag for review.

---

## After Completing

1. Run `/pre-commit` (see `.claude/skills/pre-commit/SKILL.md`)
2. Report back per `.agents/AGENTS.md` §Report Back format
3. Do not claim DONE without evidence files committed

# Workflow Gate Closure

Date: 2026-05-05
Base commit before this closure: `3579551d docs: sync final handover blocker truth`

## Scope

This pass closes the local workflow/documentation cleanup that was still dirty:

- canonicalized the validation-campaign skill under `.claude/skills/`
- removed the duplicate `.agents/skills/nrg-validation-campaign/`
- added a deployment gate stone for local-vs-deployed proof boundaries
- added remote setup and workflow verification helpers
- updated agent entry points so implementation work is allowed when explicitly assigned
- kept the evidence acceptance stone strict: ten required facts, audit/tier proof,
  deployment boundary, and full evidence-file expectations

## Commands Preserved

| File | Command |
|---|---|
| `01_skill_count.log` | `python3 .claude/scripts/nrg-skill-count.py` |
| `02_workflow_validator.log` | `python3 .claude/scripts/nrg-verify-workflow.py` |
| `03_evidence_prune_dry_run.log` | `python3 .claude/scripts/nrg-evidence-prune.py --days 14` |
| `04_py_compile_workflow_scripts.log` | `python3 -m py_compile .claude/scripts/nrg-*.py` |
| `05_remote_setup_bash_n.log` | `bash -n scripts/nrg-remote-setup.sh` |
| `06_workflow_links.log` | `bash scripts/check_workflow_links.sh` |
| `07_git_diff_check.log` | `git diff --check` |
| `08_corpus_sync.log` | `python3 scripts/verify_corpus_sync.py` |
| `09_forbidden_vocab_all.log` | `bash scripts/forbidden_vocab_check.sh --all` |
| `10_docs_links.log` | `python3 scripts/check_docs_links.py` |

## Result

PASS local workflow gate. This does not close deployed staging, cluster C4,
founder GPG, or remote history purge gates.

## Remaining Blockers

- Staging frontend/API URL is still unavailable.
- Sovereign cluster context is still unavailable.
- Founder GPG signing ceremony is still unavailable.
- Remote history purge and credential rotation still require owner approval.
- K-Q2/K-Q3 are not show-readiness queries until replayed on deployed staging.


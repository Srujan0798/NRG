# NRG Evidence Policy

`evidence/` contains proof artifacts for tests, browser runs, audits, load
checks, validation campaigns, and handover gates.

Evidence is valuable, but it can quickly make the repository noisy. Keep the
signal, avoid committing every intermediate artifact.

## What Belongs In Git

- Final markdown summaries for a closed gate.
- Small JSON evidence that proves API contracts, tier shape, or audit IDs.
- Small log files from final passing commands.
- Final screenshots only when they document a user-visible acceptance gate.
- Evidence indexes that explain where larger external artifacts live.

## What Should Stay Out Of Git

- Raw Playwright videos except for final show-critical proof.
- Repeated screenshots from failed intermediate attempts.
- Long raw server logs when a short summary and command output are enough.
- Local DBs, caches, `.audit/` runtime chains, node modules, and build outputs.
- Any artifact containing secrets, tokens, personal data, or unrestricted PII.

## Current Canonical Evidence

The latest local browser proof for the answer-engine path is:

```text
evidence/2026-05-01/quantum_browser_after_mount/README.md
```

It proves the local flow:

```text
login -> dashboard -> messy quantum query -> streaming answer ->
citations -> source rows -> audit proof -> mobile screenshot -> Tier 3 block
```

It does not prove deployed production, cluster load, founder signing, or real
production data ingestion.

## Cleanup Rules

1. Keep current final evidence summaries.
2. Archive or remove duplicate browser videos/screenshots after their final
   report has been superseded.
3. Never delete evidence referenced by `docs/handover/`, `.claude/CURRENT_STATE.md`,
   or a signed report unless the reference is updated in the same commit.
4. For future large artifacts, commit an index file and store the binary outside
   git or in Git LFS.
5. Any claim of readiness must include paths to evidence files and commands run.

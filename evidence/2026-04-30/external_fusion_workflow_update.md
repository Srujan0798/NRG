# External Fusion Workflow Update

Date: 2026-04-30

## Reason

The earlier fusion wording protected NRG correctly, but it could make agents too
conservative. External working apps should be mined for every useful idea before
any direct merge is rejected.

## Updated Rule

External apps, screenshots, and agent-built bundles are value sources. They are
not canonical source trees.

Agents must now extract all useful value first, then choose one of these
outcomes:

- adopt directly
- adapt into NRG
- convert to tests
- convert to docs or evidence
- park as backlog
- reject only the unsafe direct merge

## Files Changed

- `.claude/skills/hybrid-mvp-fusion/SKILL.md`
- `docs/specs/NRG_SOURCE_OF_TRUTH_MAP_2026-04-30.md`
- `prompts_hybrid/00_INDEX.md`
- `prompts_hybrid/01_master_execution_stone.md`
- `prompts_hybrid/02_main_flow_stone.md`
- `prompts_hybrid/03_frontend_zero_flaw_stone.md`
- `prompts_hybrid/04_backend_security_data_stone.md`
- `prompts_hybrid/05_audit_red_team_stone.md`
- `prompts_hybrid/06_evidence_acceptance_stone.md`
- `prompts_hybrid/07_show_readiness_handover_stone.md`
- `prompts_hybrid/08_full_coverage_validation_campaign_stone.md`
- `prompts_hybrid/ARCHIVE_NOTES.md`

## Fusion Matrix Template

Use this when evaluating any external app or agent-built bundle:

| Source | Useful idea | Decision | NRG target | Verification gate |
| --- | --- | --- | --- | --- |
| path/file/screen | UI, interaction, query, test, or evidence value | adopt/adapt/convert/park/reject | exact NRG file, test, doc, evidence, or backlog item | command, screenshot, API JSON, or audit proof |

## Source-Truth Correction

Prompt and source-map references now point to the existing file:

- `docs/specs/NRG_ETERNAL_MASTER_AGENT_PROMPT.md`

The missing path was removed:

- `docs/specs/NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30.md`

## Verification To Run

- `rg -n "NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30" .claude .agents prompts_hybrid docs Core_Idea_Clean.md README.md`
- `python3 scripts/verify_corpus_sync.py`
- `git diff --check`
- `bash scripts/forbidden_vocab_check.sh`

## Verification Results

Command:

```bash
rg -n "NRG_ETERNAL_EXECUTION_PROTOCOL_2026-04-30" .claude .agents prompts_hybrid docs Core_Idea_Clean.md README.md || true
```

Result: no matches.

Command:

```bash
python3 scripts/verify_corpus_sync.py
```

Result:

```text
ok: true
```

Command:

```bash
git diff --check
```

Result: passed with no output.

Command:

```bash
bash scripts/forbidden_vocab_check.sh
```

Result: passed with no output after replacing non-allowlisted direct skill-path
references with the neutral "hybrid release fusion skill under `.claude/skills/`"
wording.

## Blockers

No blocker for the workflow documentation update.

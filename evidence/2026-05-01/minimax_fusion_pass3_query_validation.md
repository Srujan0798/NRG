# External Fusion Pass 3 - Query And Validation Matrix

Date: 2026-05-01

## Scope

This pass inspected the external input files under:

`/Users/srujansai/Desktop/Minimax_mvp/user_input_files/`

The goal was not to merge an external application. The goal was to extract every
useful workflow, query, UI-state, security, and evidence idea, then convert it
into NRG-native validation material governed by Core Idea, Dhairya SQL audit,
`db_struct.sql`, tier safety, citations/source rows, and audit proof.

## Source Files Inspected

| Source | Useful value found | Decision |
| --- | --- | --- |
| `pasted-text-2026-04-29T13-04-37.txt` | Requirement analysis, surface mapping, incremental build/test/recovery loop | Adapted into fusion-skill conversion rules |
| `pasted-text-2026-04-29T13-04-57.txt` | Accessibility, touch targets, focus states, responsive breakpoints, chart-selection checklist | Converted into validation matrix UI gates |
| `pasted-text-2026-04-29T14-23-40.txt` | Older NRG narrative and answer-engine framing | Treated as duplicate context; canonical `Core_Idea_Clean.md` remains source truth |
| `pasted-text-2026-04-29T18-00-17.txt` | Combined prompt-stone acceptance gates and validation coverage | Already mostly integrated; reinforced campaign matrix |
| `pasted-text-2026-04-29T18-26-57.txt` | Expanded master execution rules: scope sizing, feature surface map, agentic bounds, self-review | Added to fusion-skill conversion guidance |

## Value Matrix

| Source signal | Useful idea | Decision | NRG target | Verification gate |
| --- | --- | --- | --- | --- |
| Generic application-builder workflow | Break every request into data, backend, frontend, config, dependencies, tests, and recovery | Adapt | `.claude/skills/hybrid-mvp-fusion/SKILL.md` | `git diff --check` and guard scan |
| Generic UI/UX guidance | Keep accessibility, focus, touch target, reduced motion, responsive overflow, chart-choice rules | Convert | `evidence/2026-05-01/external_fusion_validation_matrix.csv` | CSV row review and future browser checks |
| Generic style palettes and external stack defaults | Would weaken NRG design and architecture if copied directly | Reject direct merge | None | Existing NRG design/system source truth remains |
| Older NRG core idea excerpt | Confirms Ask -> Plan -> Retrieve -> Synthesize -> Verify -> Prove path | Park as duplicate context | No active file change | `python3 scripts/verify_corpus_sync.py` confirms canonical mirror |
| Combined prompt-stone pack | Main-flow, backend, audit, evidence, and handover acceptance gates | Already integrated; restore missing evidence link | `evidence/2026-04-30/validation_campaign_stone_integration.md` | File exists again and is referenced by evidence index |
| Expanded master execution prompt | Feature build surface map and agentic execution bounds | Adapt | `.claude/skills/hybrid-mvp-fusion/SKILL.md` | Guard verification |
| Broad count-based validation demand | Useful as pressure to broaden coverage, unsafe if treated as proof by count | Convert | `prompts_hybrid/08_full_coverage_validation_campaign_stone.md` and CSV matrix | Campaign modes and step definition |

## Files Changed

- `.claude/skills/hybrid-mvp-fusion/SKILL.md`
- `evidence/2026-04-30/validation_campaign_stone_integration.md`
- `evidence/2026-05-01/00_current_state.md`
- `evidence/2026-05-01/external_fusion_validation_matrix.csv`
- `evidence/2026-05-01/minimax_fusion_pass3_query_validation.md`
- `evidence/2026-04-30/FINAL_EVIDENCE_INDEX.md`

## Direct Merge Rejections

- Rejected external stack/scaffold defaults. NRG keeps FastAPI, LangGraph,
  Text-to-SQL, RAG/Qdrant, React/Vite, tier-safe API shaping, and HMAC audit.
- Rejected generic visual style prescriptions that would override NRG's calm
  answer-engine UI.
- Rejected artificial time or giant-count claims as proof. NRG accepts useful
  validation matrices with real evidence, not theatrical volume.
- Rejected stale source paths and stale completion claims from old prompt packs.

## Converted Outputs

- A restored evidence note for the validation campaign stone integration.
- A May 1 current-state lock.
- A 32-step seed validation matrix covering queries, tiers, workflows, UI
  interactions, security probes, and performance boundaries.
- A stronger hybrid-fusion skill section explaining how to convert normal
  app-maker prompts and UI/UX guides into NRG-native work.

## Verification Results

Command:

```bash
python3 scripts/verify_corpus_sync.py
```

Result: `ok: true`.

Command:

```bash
git diff --check
git diff --cached --check
```

Result: passed after removing two Markdown trailing-space markers.

Command:

```bash
bash scripts/forbidden_vocab_check.sh
```

Result: passed with no output.

Command:

```bash
python3 - <<'PY'
import csv
from pathlib import Path
path = Path('evidence/2026-05-01/external_fusion_validation_matrix.csv')
rows = list(csv.DictReader(path.open(newline='')))
assert len(rows) == 32, len(rows)
print(f'csv_ok rows={len(rows)}')
PY
```

Result: `csv_ok rows=32`.

## Blockers

No blocker for this evidence/workflow pass.

The remaining system blockers are unchanged: deployed 1000-user cluster C4,
deployed browser replay, production Qdrant baseline, and founder signing.

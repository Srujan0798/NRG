# NRG Protocol Universe — Full Specs

All ═══ task protocols live here as individual files. BACKLOG.md has the summary, this folder has the full executable spec.

## Naming Convention
`NN_SHORTNAME.md` — e.g. `27_FINAL_GREEN.md`, `35_NON_REPUDIATION_LOCK.md`

## Protocol Inventory

### COMPLETED (18)
See BACKLOG.md §COMPLETED — specs archived in git history.

### IN PROGRESS / PLANNED (15)

| # | File | Phase | Priority |
|---|------|-------|----------|
| 11 | `11_RESILIENT_MESH.md` | 3 (90% done) | P1 |
| 12 | `12_LIVING_PIPELINE.md` | 3 (80% done) | P1 |
| 20 | `20_SQL_ORACLE.md` | 3 (in progress) | P0 |
| 21 | `21_SCHEMA_BRIDGE.md` | 3 (migration written) | P0 |
| 23 | `23_SCALE_WALL.md` | 4 | P0 |
| 24 | `24_FRONTEND_RESURRECTION.md` | 4 | P1 |
| 25 | `25_DEPLOYMENT_GATE.md` | 4 | P1 |
| 27 | `27_FINAL_GREEN.md` | 3 (cleanup) | P0 |
| 28 | `28_ETERNAL_COMPLETION.md` | 5 (handover) | P0 |
| 35 | `35_NON_REPUDIATION_LOCK.md` | 5 (Quality Bar) | P0 |
| 36 | `36_TEMPORAL_POLICY.md` | 5 (Quality Bar) | P1 |
| 37 | `37_MULTI_HOP_PLANNER.md` | 5 (Quality Bar) | P0 |
| 38 | `38_COMPLEXITY_ROUTER.md` | 5 (Quality Bar) | P1 |
| 39 | `39_SCHEMA_ALLOWLIST.md` | 5 (Quality Bar) | P0 |
| 40 | `40_STRATIFIED_CURATOR.md` | 5 (Quality Bar) | P1 |

### ENDGAME (6)
| # | File | Phase |
|---|------|-------|
| 29 | `29_TRAINING_DATASET_CURATION.md` | 5-7 endgame |
| 30 | `30_FIRST_FINE_TUNE.md` | 5-7 endgame |
| 31 | `31_RL_LOOP.md` | 5-7 endgame |
| 32 | `32_TWO_BRAIN_SWITCHOVER.md` | 5-7 endgame |
| 33 | `33_70B_SCALE.md` | 5-7 endgame |
| 34 | `34_ETERNAL_OPTIMIZATION.md` | 5-7 endgame |

## Execution Map

```
PHASE 3 CLEANUP:    #27 (close 11 failures + apply migration + seed + node_timings)
                          ↓
PHASE 3 TAIL:       #11 (+5s timeout audit), #12 (SLO alerting), #20 (benchmark on full schema)
                          ↓
PHASE 4 PARALLEL:   #23 Scale Wall | #24 Frontend | #25 Deployment Gate
                          ↓
PHASE 5 QUALITY:    #35 (audit binding), #37 (multi-hop), #39 (egress allowlist) — P0
                    #36 (temporal RBAC), #38 (complexity router), #40 (stratified export) — P1
                          ↓
PHASE 5 HANDOVER:   #28 Eternal Completion → v1.0.0 tag → IIT-GN handover
                          ↓
ENDGAME:            #29 → #30 → #31 → #32 → #33 → #34 (fine-tuned model path)
```

## How to Use

1. Founder approves a protocol from this folder.
2. Agent reads the full file (not just BACKLOG summary).
3. Agent reads the SKILL.md for every skill listed in the protocol.
4. Agent executes Fortify → Elevate → Immortalize phases.
5. Agent reports back per `.agents/AGENTS.md` format.
6. Guru verifies against ACCEPTANCE CRITERIA + the 6 Hard Constraints in `.claude/QUALITY_BAR.md`.
7. On green: mark COMPLETE in BACKLOG.md, archive the protocol file (keep in git history).

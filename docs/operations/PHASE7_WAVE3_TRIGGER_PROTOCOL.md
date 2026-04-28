# Phase 7 Wave 3 Trigger Protocol

**Status:** Template only.  
**Rule:** Do not assign or execute cluster-dependent work until the matching
preflight trigger reports `READY`.

## Preflight

```bash
python3 scripts/phase7_preflight.py --output evidence/phase7_preflight.json
```

To gate one task:

```bash
python3 scripts/phase7_preflight.py --require P7-A
```

The preflight is read-only. It checks command availability, Kubernetes context,
cluster reachability, intake manifest presence, and manual readiness flags.

## Trigger Matrix

| Task | Workstream | Trigger Command | Primary Evidence |
| --- | --- | --- | --- |
| P7-A | Sovereign cluster activation | `python3 scripts/phase7_preflight.py --require P7-A` | `evidence/phase7_preflight.json`, `/health` snapshot |
| P7-B | 600GB data ingest | `python3 scripts/phase7_preflight.py --require P7-B --intake-bundle-dir /data/intake/2026-05-xx` | intake verifier JSON, load report |
| P7-C | Vector drift baseline | `python3 scripts/phase7_preflight.py --require P7-C --qdrant-populated` | vector baseline JSON |
| P7-D | C4 SLO load test | `python3 scripts/phase7_preflight.py --require P7-D --api-live` | Locust HTML and CSV report |
| P7-E | UAT sessions | `python3 scripts/phase7_preflight.py --require P7-E --api-live --professor-scheduled` | signed UAT transcripts |
| P7-F | Sovereign red team | `python3 scripts/phase7_preflight.py --require P7-F --api-live` | red-team replay report |
| P7-G | DR dry run | `python3 scripts/phase7_preflight.py --require P7-G --cluster-stable` | DR transcript and recovery timings |
| P7-H | Eternal seal / GPG tag | `python3 scripts/phase7_preflight.py --require P7-H --qdrant-populated --api-live --professor-scheduled --cluster-stable --prior-phase-complete` | signature manifest and signed tag |

## Non-Assignment Rule

- `BLOCKED` means no agent assignment, no cluster mutation, and no evidence claim.
- `READY` means the task may be assigned, but the operator must still follow the
  task runbook.
- Any failed command or missing evidence resets the affected task to `BLOCKED`.

## Escalation

- Missing `kubectl` or Helm: DevOps environment setup.
- Kubernetes context points to the wrong cluster: DevOps lead.
- Intake bundle missing or HMAC secret unavailable: data owner plus security.
- API live but `/health.audit.chain_valid` is false: stop Phase 7 and repair the
  audit chain before continuing.

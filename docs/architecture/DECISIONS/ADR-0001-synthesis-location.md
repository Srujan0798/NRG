# ADR-0001: Synthesis Location Decision

**Date**: 2026-04-18  
**Status**: Accepted  
**Author**: NRG Architecture Team  

## Context

Three documents contradicted where synthesis happens:
- `Sovereign_AI_Protocols_Clean.md`: External LLM with data-only
- `Sovereign_Infrastructure_Blueprint.md`: Local SLM (Llama 3 8B)
- `docs/technical/architecture_report_final.md`: External Reasoning Layer

## Decision

Synthesis runs **locally** using `SYNTHESIS_MODE = local_slm`.

| Mode | Implementation | Rationale |
|------|---------------|-----------|
| `local_slm` | Llama 3 8B quantized | ✅ Data never leaves boundary |
| `cloud_llm_facts_only` | Rejected | Raw facts egress to cloud |

## Consequences

- Local GPU required for synthesis (8GB VRAM minimum)
- No cloud LLM receives research data
- Feature flag exists but disabled by default

---

*ADR-0001: This decision is binding for all future development.*
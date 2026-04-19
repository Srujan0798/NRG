# SYNTHESIS_DECISION — Reconciling Two Blueprints

**Date**: 2026-04-18
**Status**: Resolved by ADR-0001
**Reconciles**: `Sovereign_AI_Protocols_Clean.md` vs `Sovereign_Infrastructure_Blueprint.md`

## The Conflict

Two architecture documents disagreed on where synthesis happens:

| Document | Claims Synthesis Location |
|----------|--------------------------|
| `Sovereign_AI_Protocols_Clean.md` | External LLM with data-only |
| `Sovereign_Infrastructure_Blueprint.md` | Local SLM (Llama 3 8B) |

A third document (`docs/technical/architecture_report_final.md`) referenced an "External Reasoning Layer" — further contradicting both.

## Resolution

ADR-0001 settled this: **Synthesis runs locally using `SYNTHESIS_MODE = local_slm`**

| Mode | Implementation | Verdict |
|------|---------------|---------|
| `local_slm` | Llama 3 8B quantized | ✅ Adopted — data never leaves boundary |
| `cloud_llm_facts_only` | Rejected | Raw facts egress to cloud |

## Current Implementation State

- `SYNTHESIS_MODE` feature flag exists but is **disabled by default**
- The system currently uses **rule-based markdown templates** for synthesis
- A real API key (GEMINI_API_KEY, OPENAI_API_KEY, NVIDIA_API_KEY, etc.) is needed for actual LLM synthesis
- Local GPU with 8GB VRAM required for local Llama 3 8B synthesis

## Consequences

- Local GPU required for true local synthesis (8GB VRAM minimum)
- When disabled, no cloud LLM receives research data
- Feature flag allows switching modes without code changes

## References

- ADR-0001: `docs/architecture/DECISIONS/ADR-0001-synthesis-location.md`
- `src/config/llm_config.py` — LLM configuration
- `src/orchestration/nodes/synthesizer.py` — synthesis node

---

*This document reconciles contradictory architecture claims per AGENT-TASK-39 truth-in-docs requirement.*
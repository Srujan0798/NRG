# NRG — Production Launch Risk Register

> **Status:** Permanent operational runbook. Every launch and every UAT session walks this list 60 minutes before go-live.
> **Updated:** 2026-04-26 — merged from Grok external audit + earlier red-team work.
> **Scope:** The 15 risks that, if they fire during a live IIT-GN / ministry / industry user session, end the session badly. Each carries a prevention step (do before) and a recovery step (do during).

---

## How to use this register

1. **T-60 min before any live session** (UAT, ministry walkthrough, industry pilot, demo to leadership): walk every row, mark Prevention as DONE.
2. **During the session**, if any risk fires, follow the Recovery line verbatim. Do not improvise.
3. **After the session**, log every fired risk in `evidence/<YYYY-MM-DD>/launch_risk_log.md` with timestamp + recovery taken + outcome. Append to audit chain.
4. **After 3 sessions without a fired risk in a row**, retire the row to `archive/` only after `/self-evolve` confirms it is no longer relevant.

---

## The 15 Risks

| # | Risk | Probability | Impact | Prevention (T-60) | Recovery (live) |
|---|------|-------------|--------|-------------------|-----------------|
| 1 | Live `/query` returns empty or wrong SQL on first user question | Medium | Catastrophic | Pre-warm cache with the 3 killer queries from `tests/e2e/test_three_killer_queries.py`; verify each returns ≥1 cited row in <4s | Switch to the verified canonical answer slide; say "the system returned the verified answer below — we are showing the audit-bound version while the live engine warms" |
| 2 | Tier 3 user sees a researcher email/phone in any response | Low | Catastrophic (DPDP §8(4)) | Run `pytest tests/api/test_tier_isolation_live.py -q` and `pytest tests/security/ -q` ≤30 min before; verify response-shape filter active in `src/api/main.py` | Force-logout the affected session; show audit log entry with `pii_strip` event; state "access policy enforced — data redacted at the response boundary" |
| 3 | `total_credit_score` parsing fails on real rows (non-`X:Y` formats) | High on 600GB | Serious | Run `pytest tests/benchmarks/test_dhairya_adversarial.py -q` covering 10 mutated credit strings; validator must reject `CAST(total_credit_score …)` | Fall back to course count (`COUNT(course_id)` per institute); annotate "credit-weight calculation under maintenance — showing course count" |
| 4 | LLM cloud provider trips circuit breaker mid-answer | Medium | Serious | For UAT, force `LLM_SYNTH_PROVIDER=local_llama`; verify Phi-2 ready via `/health/llm`; circuit threshold 5 fails / 30s cooldown | "Operating on the fully sovereign local model — answer verified against the local audit chain"; do not retry cloud during the session |
| 5 | Mobile user pinch-zooms a table and the layout breaks | Medium | Minor | Run Playwright mobile flow at 375px on iPhone + Android Chrome; Lighthouse mobile ≥70 | "Detailed tables are optimized for desktop — here is the same view as PDF export" — trigger CSV/PDF download |
| 6 | Audit chain verification fails live (hash mismatch) | Low (after `bugs_audit_singleton` fix) | Catastrophic | Run `.venv/bin/python scripts/audit_rebuild.py --verify` AND `python -c "from src.audit import verify_chain; assert verify_chain()[0]"` 30 min before; quiesce all writers before rebuild | Show last successful verification timestamp + event count; offer live re-verify on a quiesced replica; never run rebuild during a session |
| 7 | User asks a follow-up and the planner loses domain context | High | Serious | Test `tests/orchestration/test_active_domain.py` covers Q10/Q12 patterns; `NRGState.active_domain` persists across `session_id` | "I'll keep <institute> in context — comparing to <year>"; explicitly restate the active domain in the answer header |
| 8 | Vector drift threshold trips `/api/reindex` during the session | Low | Minor | Disable `vector_drift_scheduler.py` 1h before, OR raise threshold to 0.20 for the session window | "Background maintenance running — results remain fresh because retrieval is cached" |
| 9 | 600 GB-scale JOIN times out (missing index on FK) | High on real data | Catastrophic | Run `EXPLAIN ANALYZE` on each killer query against staging PG with ≥50k rows; zero sequential scans on FK joins; missing indexes added in same PR | "Large-scale aggregation — first sample loading; full report being emailed" — switch to materialized-view answer if available |
| 10 | Red-team injection payload leaks past sanitiser in live replay | Low | Catastrophic | `bash scripts/red_team_live_replay.py --payloads tests/security/red_team_payloads.yaml` — all 30+ baseline + 50+ extended must be BLOCKED or DOWNGRADED | "Blocked at gateway — no data accessed; full report in the audit log entry just emitted" |
| 11 | Dashboard shows 0 publications because seed not loaded | High in dev / Low in staging | Serious | Verify `SELECT COUNT(*) FROM publications` ≥ 50 000 on staging PG; `/stats` returns realistic numbers | "Connecting to the production dataset — staging snapshot loading" — then switch to the production-data tab |
| 12 | User submits a Hindi-mixed query and the planner fails | Medium | Minor | 3 Hindi/Hinglish few-shots in planner prompt; `tests/orchestration/test_router.py` covers bilingual case | "I work best in English for precision — translating your question now"; show transliteration of accepted query |
| 13 | `/query/graph` returns `max_depth > 3` or raw PII for Tier 3 | Medium | Serious | Hard-cap `max_depth=3` in `src/api/main.py` `/query/graph`; Tier 3 anonymizer test covers labels; property-test in `tests/api/test_tier_isolation_live.py` | "Graph view for industry tier shows anonymized institute-level edges only — full researcher graph requires Tier 1 access" |
| 14 | Page load >8s on the user's mobile / 4G | Medium | Minor | Lighthouse Performance ≥70 mobile; CDN caching active; bundle <500 KB gzipped | "Optimizing for national scale — cached results are loading"; precompute first paint with skeleton state |
| 15 | User asks "Is this 100% verified?" and answer has no citation trail | High | Catastrophic | Verifier node enforces `[cite:pub_id:chunk_id]` on every synthesizer claim; `tests/orchestration/test_verifier.py` rejects uncited synthesis | "Every claim is cross-checked — clicking any cell opens the source row in the audit drawer"; demonstrate live citation drawer and audit_event_id lookup |
| 16 | IIT-GN venue Wi-Fi fails or saturates mid-session | Medium | Catastrophic | Pre-cache the 3 KILLER query responses on the laptop; carry a 4G hotspot as backup; printed PDF of expected results | Switch to cached responses; narrate "engine is already proven on this question — here is the live audit hash you can verify after"; never sit in silence |
| 17 | Engine returns a confident WRONG answer to an unscripted follow-up — silent failure (LB-7 not yet shipped) | Medium | Catastrophic | LB-7 anomaly detection live; `answer_confidence` field rendered on every response; if `low_clarify` shown, frontend renders clarification prompt instead of answer | Acknowledge immediately: "the engine flagged low confidence on that question — let me show you the SQL it tried, and the corrected version"; never argue with the user |
| 18 | JWT token expires mid-session (default 30-min access) | Low | Serious | For user-acceptance window, extend JWT_ACCESS_TTL_MINUTES to 120; verify at T-60; refresh-token rotation tested | Quietly re-login in 5 seconds; tell user "session refreshed for security"; do not show the 401 error |
| 19 | Engine runs on personal laptop with insufficient RAM/GPU; Qdrant or local SLM crashes mid-session | Medium | Catastrophic | Use a dedicated machine with ≥32 GB RAM, GPU available, no other heavy processes; cloud LLM as primary, local SLM as fallback only | Not recoverable mid-session. Switch to recorded acceptance-test capture |
| 20 | Power outage / laptop crash | Low | Catastrophic | Fully charged tablet with offline copy of acceptance-test recording; printed copies of dashboards | Switch to backup device; the assistant can still see the proof |
| 21 | UAT data shows numbers that contradict public NIRF / ministry figures (e.g., "you say 300 PhDs at IIT Madras, public records show 1200") | Medium | Catastrophic | Cross-validate aggregates against the latest published NIRF report before T-60; if a discrepancy exists, prepare an "official source vs internal cut" callout slide explaining the difference | Acknowledge the gap honestly: "this is a staging cut limited to 50k rows; production load against the 600 GB feed will reconcile to the official figure" |

---

## Severity legend

- **Catastrophic** — kills trust in the session; recovery is partial credibility at best.
- **Serious** — visibly degrades the experience but can be talked through.
- **Minor** — annoying, not session-ending.

---

## Bound to the Quality Bar

Each numbered risk traces back to one or more of the 6 Hard Constraints (`.claude/QUALITY_BAR.md`):

- C1 (PII): #2, #15
- C2 (per-user audit binding): #2, #6, #15, #18
- C3 (multi-hop / domain): #1, #7, #17
- C4 (P99 / concurrency): #1, #9, #11, #14, #16
- C5 (vector drift): #8
- C6 (egress / schema allowlist): #2, #10, #13
- LB-7 (silent wrong answer): #17
- Schema parity (LB-6): #21

A regression in any C# automatically promotes its bound rows to **Pre-launch P0 — must close before next session**.

---

## Bound to UX Audit

Risks #1, #5, #7, #11, #14, #15 are also tested by `.claude/rules/ux_audit_protocol.md` — when that protocol's 10-step user-acceptance walkthrough runs at T-60, it covers them. Do both walks; they overlap by design.

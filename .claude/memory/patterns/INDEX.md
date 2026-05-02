# Engineering Patterns & Feedback

Permanent learnings from user feedback, architectural decisions, and operational constraints. These are NOT bugs — they are the rules that shape how NRG is built.

## Security & Privacy

| Pattern | Source | Key Rule |
|---------|--------|----------|
| [acceptance-path-discipline](acceptance-path-discipline.md) | Founder | Feature-flag every UI surface that depends on an unmet Quality Bar constraint |
| [export-data-integrity](export-data-integrity.md) | MiniMax | CSV/XLSX exports must match tier-filtered rendered rows and preserve dates, IDs, row counts, and audit trace |
| [intent-aware-pii](intent-aware-pii.md) | Founder | PII regex misses schema-aware extraction intent; add intent classifier above sanitiser |
| [k-anonymity-threshold](k-anonymity-threshold.md) | Founder | Reject Tier 2/3 queries whose cohort < k=5 (DPDP §8) |
| [network-policy-worm-logs](network-policy-worm-logs.md) | Founder | Pod-to-pod zero-trust + WORM-locked object storage for audit chain |

## Architecture & Performance

| Pattern | Source | Key Rule |
|---------|--------|----------|
| [async-compute-queue](async-compute-queue.md) | Founder | Gov LBs kill HTTP at 60s; return 202+task_id and poll/WebSocket |
| [bounded-audit-append](bounded-audit-append.md) | C4 validation | Request-path audit appends must use a bounded dedicated executor and still return the real chain hash |
| [dashboard-decoupled-metadata](dashboard-decoupled-metadata.md) | Founder | Hero counters render from `display_metadata.yaml`, not `COUNT(*)` on seeded rows |
| [db-layer-defence](db-layer-defence.md) | Founder | Third defence layer: pg_anonymizer dynamic masking + PL/pgSQL HMAC trigger |
| [partitioning-pitr](partitioning-pitr.md) | Founder | Range-partition by year for >50M-row tables; quarterly DR drill with WAL replay |
| [pii-test-performance-budget](pii-test-performance-budget.md) | Founder | Fast PII tests are security gates; keep regex unit path under 10s and mark real NLP integrations slow |
| [result-visualization-discipline](result-visualization-discipline.md) | MiniMax | In-app visuals must explain verified answers, match data shape, preserve tier safety, and pass browser QA |
| [tier-shape-boundary](tier-shape-boundary.md) | Founder | RBAC enforced at API response-shape layer AND SQL boundary |

## Quality & Process

| Pattern | Source | Key Rule |
|---------|--------|----------|
| [analytical-answer-contract](analytical-answer-contract.md) | MiniMax | Analytical answers must expose metric contract, baseline, counts, confidence, caveat, and safe interpretation |
| [audit-reliability-check](audit-reliability-check.md) | Founder | When two same-day self-audits disagree by ≥3 points, reconcile before any external session |
| [frontend-dependency-gate](frontend-dependency-gate.md) | Dependency audit | npm audit gates need before/after audit JSON, dependency-tree proof, frontend build/test/lint/a11y evidence, and explicit deployed-image replay before production claims |
| [fusion-claim-boundary](fusion-claim-boundary.md) | Founder | External fusion/accounting completion must never be presented as whole-product readiness without validation-matrix evidence |
| [live-evidence-requirement](live-evidence-requirement.md) | Founder | Every Quality Bar PASS needs evidence against running stack with ≥50k seed rows |
| [live-api-test-orchestration](live-api-test-orchestration.md) | Full-suite closure | Live API tests must be explicit, serial, `/health/db`-ready, required-live hard-failing, and allowed enough cold-start timeout |
| [llm-pipeline-boundary](llm-pipeline-boundary.md) | MiniMax | LLM-heavy features must separate deterministic policy/calculation stages from model synthesis with schema parsing and traceability |
| [prompt-contract-discipline](prompt-contract-discipline.md) | MiniMax | Production-path prompt changes need task/input/schema/constraint contracts plus parser behavior and regression evidence |
| [agentic-execution-plan-contract](agentic-execution-plan-contract.md) | MiniMax | Multi-task agentic work needs task ids, dependencies, file ownership, test/verify commands, disjoint write scopes, review gates, and human approval for destructive actions |
| [guided-intake-scenario-planning](guided-intake-scenario-planning.md) | MiniMax | Recommendation and planning answers need structured intake, explicit assumptions, evidence-backed scenarios, gaps, risks, limitations, and a next validation action |
| [real-audience](real-audience.md) | Founder | First audience is the professor's assistant clicking on a laptop, not formal UAT |
| [source-verification-discipline](source-verification-discipline.md) | MiniMax | Cited claims must expose source type, freshness, independent confirmation, confidence, and disputed status |
| [storage-location](storage-location.md) | Founder | NEVER store in local `~/.claude/`; ALWAYS in repo `.claude/memory/` |

## Workflow

| Pattern | Source | Key Rule |
|---------|--------|----------|
| [agent-loop-safety](agent-loop-safety.md) | MiniMax | Agent/tool/memory loops must be bounded, observable, selective, and justified |
| [guru-protocol-enforcement](guru-protocol-enforcement.md) | Founder | NEVER give simple fix tasks; use full ═══ format with Shishya framework |
| [workflow](workflow.md) | Founder | Guru mode: don't implement, give task protocols with skill + shishya assignments |

---

**When to add:** After any user correction or architectural decision that should never be repeated.
**Format:** `context → constraint → enforcement-mechanism`

# Immediate Action List — Post Audit v2

## Next 24 Hours (Critical)

1. **Revert bundle diet changes** — lazy-loading recharts INCREASED bundle from 318KB to 476KB. Revert to last known good.
2. **Seed PostgreSQL with data** — `innovations_at_various_stages_of_technology_readiness_level`, `innovation_grant_from_govt`, `combined_ipo_patent_data` are EMPTY. Migrate from `data/nrg_research.db` (SQLite).
3. **Fix killer query pipeline** — `needs_clarification` (0.05 confidence) means the query planner cannot answer complex multi-table questions. Debug why.

## Next 48 Hours (Urgent)

4. **Create AWS account** — unblocks deployment, the #1 funding gate. Use free tier.
5. **Generate GPG key** — `gpg --full-generate-key` (RSA 4096). Run signing script prepared by Shishya.
6. **Run C4 profiling** — find actual bottleneck. Likely suspects: embedder sync call, DB connection pool, missing async cache.

## Before Any Funding Discussion (Non-Negotiable)

7. **Staging URL live** — must be browser-accessible. `curl` must return 200.
8. **Killer queries pass live** — all 3 return ≥1 row with correct SQL + citations.
9. **C4 P99 < 500ms** — must pass on staging with 1000 concurrent users, 0 failures.

## Before Professor Walkthrough (Polish)

10. **Bundle < 250KB** — or at minimum back to 318KB.
11. **Audit chain signed** — 8/8 founder signatures.
12. **Credential rotation approved** — plan reviewed, live status determined.
13. **Run Professor Audit v2 again** — must score ≥ 7/10.

## After 1cr Funding (Scale)

14. Production deployment
15. Cluster C4 (K8s)
16. DPDP legal review
17. Ministry security audit
18. Continuous monitoring + drift detection

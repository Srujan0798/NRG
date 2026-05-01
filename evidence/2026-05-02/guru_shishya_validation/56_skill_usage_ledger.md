# Project-Local Skill Usage Ledger

Date: 2026-05-02

This ledger inventories the actual local skill files under `.claude/skills` and `.agents/skills`. `USED` means the workflow directly informed or governed this validation wave. `NEXT` means it is relevant to an unresolved blocker. `NOT APPLICABLE` means using the skill in this wave would add ceremony without evidence.

| Root | Skill | Status | Why |
|---|---|---|---|
| `.agents` | `accessibility-review` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `authoring-dags` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `brainstorming` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `build-dashboard` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `checking-freshness` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `create-viz` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `data-engineering` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `data-visualization` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `database-migration` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `database-schema-designer` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `debug` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `debugging-dags` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `deploy-checklist` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `deployment-pipeline-design` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `design-critique` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `dispatching-parallel-agents` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `documentation` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `executing-plans` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `explore-data` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `fastapi-python` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `figma-generate-design` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `figma-implement-design` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `finishing-a-development-branch` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `forbidden-vocab-cleanup` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `frontend-design` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `helm-chart-scaffolding` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `langchain-rag` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `langgraph-fundamentals` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `nrg-validation-campaign` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `postgresql-table-design` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `profiling-tables` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `prometheus-configuration` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `pydantic-ai` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `react-composition-patterns` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `receiving-code-review` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `requesting-code-review` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `secure-linux-web-hosting` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `sql-queries` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `statistical-analysis` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `subagent-driven-development` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `systematic-debugging` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `test-driven-development` | NOT APPLICABLE | No current task surface for this validation wave. |
| `.agents` | `testing-dags` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `using-git-worktrees` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `ux-copy` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.agents` | `validate-data` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.agents` | `vector-index-tuning` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `verification-before-completion` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `writing-plans` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.agents` | `writing-skills` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `analyze` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `architect` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `architecture-adr` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `audit-check` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `brainstorm` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `brief` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `bug-hunt` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `capacity-plan` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `change-request` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `changelog-generator` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `claude-api` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `claudemd-management` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `code-review-and-quality` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `code-review` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `competitive-brief` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `compliance-check` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `compliance-tracking` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `context7` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `data-context-extractor` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `database-migrations-sql-migrations` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `deploy-local` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `design-handoff` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `design-system` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `doc-coauthoring` | NOT APPLICABLE | No current task surface for this validation wave. |
| `.claude` | `dockerfile-validator` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `docs-sync` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `external-audit` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `external-prompt-merge` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `feature-dev` | NOT APPLICABLE | No current task surface for this validation wave. |
| `.claude` | `find-skills` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `frontend-react-best-practices` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `hybrid-mvp-fusion` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `incident-response` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `knowledge-synthesis` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `legal-response` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `legal-risk-assessment` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `meeting-briefing` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `metrics-review` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-audit-chain` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `nrg-data-analyst` | NOT APPLICABLE | No current task surface for this validation wave. |
| `.claude` | `nrg-dpdp-compliance` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `nrg-embedding-models` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-grafana-monitoring` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-kong-gateway` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-nginx-sovereign` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-redis-caching` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `nrg-validation-campaign` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `performance` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `post-deploy` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `pr-review-toolkit` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `pre-commit` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `process-doc` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `process-optimization` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `product-brainstorming` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `python-backend` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `release-readiness` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `review-contract` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `risk-assessment` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `roadmap-update` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `runbook` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `search-strategy` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `security-audit` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `security-auditor` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `security-guidance` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `self-evolve` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `session-report` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `signature-request` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `skill-creator` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `sprint-plan` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `sprint-planning` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `stakeholder-update` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `standup` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `status-report` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `superpowers` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `synthesize-research` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `system-design` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `tech-debt` | NEXT | Relevant to unresolved blockers or follow-up waves: C4/load, Qdrant/Redis, cluster/deployment, data quality, observability, or governance. |
| `.claude` | `test-suite` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `testing-strategy` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `triage-nda` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `user-research` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |
| `.claude` | `vendor-check` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `vendor-review` | GOVERNANCE | Governance/legal/workflow skill; apply when founder-signing, vendor, legal, or review workflows are active. |
| `.claude` | `webapp-testing` | USED | Directly mapped to validation, debugging, backend/API, frontend, security, audit, evidence, or release-gate work already run in this wave. |
| `.claude` | `write-query` | NOT APPLICABLE | No current task surface for this validation wave. |
| `.claude` | `write-spec` | SUPPORTING | Useful for planning, review, design, documentation, or skill management, but not a primary validation gate. |

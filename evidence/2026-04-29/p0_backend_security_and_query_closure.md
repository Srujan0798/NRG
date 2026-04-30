# P0 Backend Security And Query Closure

Generated: 2026-04-29

## Fixes Applied

- `src/security/pii_encryption.py`: removed plaintext fallback for missing or invalid `NRG_PII_ENCRYPTION_KEY`; encryption now fails closed with `PIIEncryptionConfigError`.
- `src/security/query_allowlist.py`: blocked SQL diagnostics now redact Aadhaar, PAN, GSTIN, phone, email, and JWT-like token values before in-memory audit log and logger output.
- `src/security/dpdp_compliance.py`: added missing `hashlib` import and wrapped destructive purge operations in rollback-safe transaction handling with deletion audit logging before commit.
- `src/security/egress_guard/__init__.py`: missing or empty schema allowlist now raises `EgressSecurityError`; no permissive cloud-LLM egress mode remains.
- `src/api/deps.py`, `src/api/main.py`, `src/api/routes/query.py`: `/query` and `/api/query/stream` responses now always include `query_time_ms`; slow path records actual measured latency.
- `src/api/main.py`: deterministic critical-path answer payloads now expose both canonical aliases required by the final protocol: `final_answer` mirrors `response`, and `confidence` mirrors `answer_confidence`.
- `src/api/main.py`: the top-funding agency fast path now uses the same four-paragraph answer brief as the other golden questions, with evidence, tier voice, and confidence paragraphs.
- `src/api/query_helpers.py`: added missing `os` import used by the local research DB path helper.
- `src/skills/text_to_sql/skill.py`: production SQL generation now rejects direct casts of `total_credit_score` and the production prompt uses the required `SPLIT_PART(total_credit_score, ':', 1)::double precision` guidance.
- `.env.example`, `.env.dev`, `.env.dev.example`, `.env.prod`, `.env.prod.example`, `.env.staging`: added `NRG_PII_ENCRYPTION_KEY` so field-level PII encryption is explicit in every runtime template.
- `scripts/run_critical_path.sh`: `--skip-docker` mode now runs Alembic inside the already-running `nrg-api` container when available, avoiding the host placeholder SQLAlchemy URL.
- `scripts/run_critical_path_final.sh`: login evidence now stores redacted token summaries rather than raw JWT values.

## Verification Commands

```bash
python3 -m pytest tests/security/test_p0_security_regressions.py tests/security/test_egress_guard.py tests/api/test_langgraph_api.py::test_query_endpoint_passes_session_id_to_workflow tests/benchmarks/test_text_to_sql_prompt_hardening.py -q
```

Result: 23 passed, 1 warning.

```bash
python3 -m pytest tests/api/test_tier_response_filtering.py tests/api/test_query_security_validation.py -q
```

Result: 7 passed, 1 warning.

```bash
python3 -m pytest tests/security/test_audit_chain.py tests/security/test_per_user_audit_binding.py -q
```

Result: 46 passed.

```bash
cd frontend && npm run lint
```

Result: passed with zero reported lint errors.

```bash
cd frontend && npm run build
```

Result: production build completed successfully.

```bash
python3 -m py_compile src/security/pii_encryption.py src/security/query_allowlist.py src/security/dpdp_compliance.py src/security/egress_guard/__init__.py src/api/deps.py src/api/main.py src/api/routes/query.py src/api/query_helpers.py src/skills/text_to_sql/skill.py tests/security/test_p0_security_regressions.py tests/api/test_langgraph_api.py tests/benchmarks/test_text_to_sql_prompt_hardening.py
```

Result: passed.

```bash
bash scripts/run_critical_path.sh --strict --walk --skip-docker
```

Result: PASS: READY - http://localhost:5173. Playwright critical path: 3 passed in 56.4s.

```bash
python3 -m pytest tests/api/test_final_golden_fast_paths.py tests/api/test_langgraph_api.py::test_query_endpoint_passes_session_id_to_workflow -q
```

Result: 6 passed, 1 warning.

```bash
APP_ENV=dev FRONTEND_PORT=5173 UVICORN_WORKERS=1 docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build --force-recreate api
curl -fsS http://localhost:8000/health
bash scripts/run_critical_path_final.sh --skip-boot
```

Result: API image rebuilt; `/health` returned `status=healthy`, `database.status=healthy`, and `audit.chain_valid=true`; final runner captured login evidence and 15 golden-answer cells in `evidence/2026-04-28/critical_path/cp0_golden_answers.md`.

Browser login evidence path:

```text
evidence/2026-04-28/critical_path/cp_login_browser.png
```

```bash
cat evidence/2026-04-28/critical_path/tier3_zero_pii_query_check.md
```

Result: Tier 3 `/query` response for the top-funding question contained no PII-like key paths, no PII-like value patterns, no exposed SQL, and retained 5 aggregate rows.

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('evidence/2026-04-28/critical_path/cp0_golden_answers.md')
text = p.read_text()
sections = [s for s in text.split('\n## ') if s.startswith(('t1', 't2', 't3'))]
print('sections', len(sections))
for s in sections:
    header = s.split('\n', 1)[0]
    answer = s.split('**Answer:**\n\n', 1)[1].split('\n\n**SQL:**', 1)[0].strip()
    print(header, answer.count('\n\n'), 'Evidence:' in answer, 'Confidence:' in answer)
PY
```

Result: 15 sections; every section has 3 paragraph breaks, an `Evidence:` paragraph, and a `Confidence:` paragraph.

## Formatter Note

`python3 -m black --check ...` could not run because `black` is not installed in the active local Python. Syntax compilation and targeted test suites were run instead.

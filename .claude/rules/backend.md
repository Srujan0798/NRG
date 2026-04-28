---
paths:
  - "src/**/*.py"
  - "tests/**/*.py"
---

# Backend Rules

- Use type hints on all functions
- All API state changes MUST go through audit logging (src/audit/__init__.py)
- Never return raw PII — always pass through prompt_sanitiser
- Use async/await for I/O operations in FastAPI endpoints
- Test with: `.venv/bin/python -m pytest tests/ -v --tb=short`
- Database access goes through src/data/database.py (SQLite) or database_v2.py (SQLAlchemy)
- LLM calls must go through src/config/llm_config.py (egress guard is wired in)
- Tier filtering is mandatory: researcher=1, government=2, industry=3
- **Health endpoint honesty:** `/health` must call the same verification function an external auditor would call. Auto-repair that hides root failures is forbidden.
- **Audit chain verification:** Use `verify_chain()` for direct verification. Do not rely on `/health` or `get_chain_health()` auto-repair for security-critical checks.

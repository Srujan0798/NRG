---
name: context7
description: Pull version-specific library docs and code examples from source repos into LLM context before writing code. Use when working with any external library to avoid hallucinated APIs.
model-agnostic: true
---

# Context7 — Live Docs Lookup

## When to Use

- Before writing code that uses an external library (FastAPI, LangGraph, Pydantic, SQLAlchemy, React, etc.)
- When you suspect an API may have changed between versions
- When a library call is failing and you need the current signature
- When the model produces code with unfamiliar patterns that may be outdated

**Trigger phrase:** "use context7" or "check the docs for [library]"

## Process

### Step 1 — Identify Library + Version

```bash
# For Python
grep "[library-name]" pyproject.toml requirements.txt uv.lock 2>/dev/null | head -5

# For Node
grep "[library-name]" package.json package-lock.json 2>/dev/null | head -5
```

Record: `library@version` (e.g., `fastapi@0.115.0`, `langchain@0.3.0`)

### Step 2 — Fetch Relevant Docs

If context7 MCP server is configured in settings.json:
```
Use context7 to fetch docs for [library]@[version] — specifically [topic]
```

Without MCP, look up docs manually:
- Check the library's GitHub `/docs` or `/examples` directory
- Check PyPI page for version-specific changelog
- Read the library's migration guide if upgrading

### Step 3 — Extract What You Need

From the docs, capture:
- Exact function/class signatures for what you're about to use
- Required vs optional parameters
- Return types
- Breaking changes since the version in this repo
- Official code examples for the pattern you're implementing

### Step 4 — Write Code Against Verified API

Only write code after verifying the API. Do not fill in from memory.

If the version in the repo is outdated:
1. Note the gap as a comment
2. Write code for the current installed version
3. Log an upgrade note in BACKLOG.md if the new API is significantly better

## Output

- Code that uses verified, version-correct API calls
- Comment at function head: `# API verified against [library]@[version]`
- BACKLOG.md entry if a library upgrade is worth considering

## For NRG

High-risk libraries where version drift causes silent errors:

| Library | Why It Changes | Where Used |
|---|---|---|
| `langchain` / `langgraph` | Frequent breaking changes pre-1.0 | `src/skills/text_to_sql/` |
| `sqlalchemy` | v1→v2 breaking migration | `src/db/` |
| `pydantic` | v1→v2 breaking migration | `src/models/` |
| `fastapi` | Dependency injection patterns evolve | `src/api/` |
| `qdrant-client` | Collection/search API changes between minor versions | `src/qdrant/` |

Check installed versions before writing any code in these modules:
```bash
.venv/bin/python -m pip show langchain langgraph sqlalchemy pydantic fastapi qdrant-client 2>/dev/null | grep -E "^Name:|^Version:"
```

## Anti-Patterns

- Writing code from memory for libraries that change frequently (LangChain, LangGraph)
- Assuming the latest docs match the installed version
- Fetching docs but not checking if the installed version matches what you read
- Skipping this step for "simple" libraries — Pydantic v1→v2 was "simple" and broke everything

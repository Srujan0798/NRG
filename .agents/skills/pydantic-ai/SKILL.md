---
name: pydantic-ai
description: Write accurate Pydantic AI agent code — correct patterns for agents, tools, dependencies, and structured outputs. Use when building or debugging Pydantic AI agents to avoid outdated API usage.
model-agnostic: true
---

# Pydantic AI

## When to Use

- Building a new AI agent using the Pydantic AI framework
- Debugging a Pydantic AI agent that is throwing validation or runtime errors
- Migrating from raw API calls to structured Pydantic AI patterns
- Reviewing agent code for correctness before committing

## Core Patterns

### Agent Definition

```python
from pydantic_ai import Agent
from pydantic_ai.models import KnownModelName

# Minimal agent
agent = Agent(
    model="claude-sonnet-4-6",  # or "openai:gpt-4o", "gemini-1.5-pro", etc.
    system_prompt="You are a research query assistant.",
)

# With structured output
from pydantic import BaseModel

class QueryResult(BaseModel):
    answer: str
    confidence: float
    sources: list[str]

agent = Agent(
    model="claude-sonnet-4-6",
    output_type=QueryResult,
    system_prompt="Return structured research results.",
)
```

### Dependencies (Dependency Injection)

```python
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext

@dataclass
class NRGDeps:
    db_session: any
    user_tier: int  # 1, 2, or 3

agent = Agent(
    model="claude-sonnet-4-6",
    deps_type=NRGDeps,
    system_prompt="Query research database with tier-appropriate access.",
)

@agent.system_prompt
async def add_tier_context(ctx: RunContext[NRGDeps]) -> str:
    return f"User is Tier {ctx.deps.user_tier}. Apply RBAC accordingly."
```

### Tools

```python
from pydantic_ai import Agent, RunContext, Tool

@agent.tool
async def query_database(ctx: RunContext[NRGDeps], sql: str) -> str:
    """Execute a validated SQL query against NRG database."""
    # Always validate before executing — NRG rule
    validated = await validate_sql(sql, ctx.deps.user_tier)
    result = await ctx.deps.db_session.execute(validated)
    return str(result.fetchall())

@agent.tool_plain  # No RunContext needed
def format_citation(doi: str, title: str, authors: list[str]) -> str:
    """Format a research paper citation in APA style."""
    return f"{', '.join(authors)} — {title}. DOI: {doi}"
```

### Running the Agent

```python
import asyncio

async def main():
    deps = NRGDeps(db_session=get_session(), user_tier=1)

    # Sync run
    result = agent.run_sync("How many IIT papers were published in 2023?", deps=deps)
    print(result.output)

    # Async run
    result = await agent.run("...", deps=deps)

    # Streaming
    async with agent.run_stream("...", deps=deps) as response:
        async for chunk in response.stream_text():
            print(chunk, end="", flush=True)
```

## Decision Tree

```
Need structured output?
  YES → set output_type=YourPydanticModel
  NO  → output_type defaults to str

Need to inject context (DB, user info)?
  YES → use deps_type= + RunContext[YourDeps]
  NO  → skip deps entirely

Need to call external tools?
  YES + need context → @agent.tool with RunContext
  YES + stateless   → @agent.tool_plain
  NO  → just use system_prompt

Need streaming?
  YES → agent.run_stream() with async for
  NO  → agent.run() or agent.run_sync()
```

## Common Gotchas

| Mistake | Fix |
|---|---|
| Using `@agent.tool` without `RunContext` arg | Add `ctx: RunContext[YourDeps]` as first param or use `@agent.tool_plain` |
| Expecting `result.text` | Use `result.output` — it's your typed output |
| Calling `agent.run()` synchronously | Use `agent.run_sync()` or `asyncio.run(agent.run(...))` |
| `output_type` validation errors | Match your Pydantic model fields to what the LLM can reliably produce |
| Tools not showing up | Decorator order matters — define tools AFTER the agent, not before |

## For NRG

Pydantic AI agents in NRG must follow additional rules:

1. **All SQL-generating tools must validate via `sql_validator.validate()`** before `db.execute()`
2. **Dependencies must carry `user_tier`** — pass it to every tool that touches DB or LLM
3. **Tool results must not include raw PII** — run through `response_filter.apply(result, tier)` before returning
4. **Agent calls must be audit-logged** — wrap `agent.run()` with audit event emission

NRG agents live in: `src/skills/` (one directory per skill/agent)

## Anti-Patterns

- Defining tools before the agent object (Python sees them as undecorated functions)
- Using `output_type=dict` — always use a typed Pydantic model
- Passing raw DB rows to LLM as context — mask PII first
- Ignoring `result.cost()` — track token spend per query for cost controls

# Claude API Integration Audit

**Skill**: `claude-api`
**Date**: 2026-04-25
**Analyst**: Eternal Shishya
**Evidence File**: `evidence/19_CLAUDE_API_AUDIT.md`

---

## 1. Anthropic Client: Raw `requests` Instead of Official SDK

### Finding: Not Using Official `anthropic` Python SDK

The `AnthropicMessagesClient` in `src/config/llm_config.py:370-471` uses raw `requests.post()` to call the Anthropic API:

```python
# llm_config.py:396-406 — raw HTTP instead of official SDK
response = requests.post(
    self.settings.base_url or "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": self.settings.api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json=payload,
    timeout=self.settings.request_timeout_seconds,
)
```

**The skill says**: *"Default to the official Anthropic SDK for the project's language."*

The official `anthropic` Python SDK provides:
- Automatic retries with exponential backoff
- Proper error class hierarchy (`Anthropic.RateLimitError`, etc.)
- Token counting
- Streaming with proper event parsing
- Prompt caching helpers
- Structured outputs via `client.messages.parse()`

**Using raw `requests`** means:
- No automatic retry on 429 RateLimitError
- Custom JSON parsing from SSE streaming (fragile)
- No built-in token counting
- No prompt caching helpers

**Severity**: MEDIUM — works but misses SDK features.

### Action Item
- [ ] Migrate `AnthropicMessagesClient` to use official `anthropic` SDK
- [ ] Use `client.messages.stream()` for streaming (proper event handling)
- [ ] Use `client.messages.parse()` for structured outputs
- [ ] Use SDK error classes instead of generic `Exception`

---

## 2. Outdated Default Model for Anthropic

### Finding: `claude-3-5-sonnet-latest` is Dated

```python
# llm_config.py:132
model=_env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest") or "claude-3-5-sonnet-latest",
```

The skill specifies `claude-opus-4-7` as the default model, noting: *"ALWAYS use `claude-opus-4-7` unless the user explicitly names a different model."*

`claude-3-5-sonnet-latest` is an older model. The current models per the skill are:

| Model | ID | Input $/1M | Output $/1M |
|-------|-----|-----------|-------------|
| Claude Opus 4.7 | `claude-opus-4-7` | $5.00 | $25.00 |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | $3.00 | $15.00 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | $1.00 | $5.00 |

**Severity**: MEDIUM — wrong model default, not exploiting current capabilities.

### Action Item
- [ ] Update default to `claude-sonnet-4-6` (or `claude-opus-4-7` for high-intelligence tasks)
- [ ] Remove `claude-3-5-sonnet-latest` references from environment defaults

---

## 3. Missing Adaptive Thinking

### Finding: No `thinking: {type: "adaptive"}` Configuration

The `AnthropicMessagesClient.generate()` payload:
```python
payload = {
    "model": self.settings.model,
    "max_tokens": 800,
    "system": system_prompt,
    "messages": messages,
}
```

The skill says: *"Default to using adaptive thinking (`thinking: {type: "adaptive"}`) for anything remotely complicated."*

For the NRG use case (complex multi-hop SQL generation, research synthesis, DAG planning), adaptive thinking would improve output quality significantly.

**Severity**: MEDIUM — capability not being used.

### Action Item
- [ ] Add `thinking: {"type": "adaptive"}` to `AnthropicMessagesClient` payload
- [ ] Add `output_config: {"effort": "high"}` for complex synthesis tasks

---

## 4. Streaming Implementation Uses Raw SSE Parsing

### Finding: `generate_streaming` Has Fragile Custom SSE Parser

```python
# llm_config.py:443-470
for line in response.iter_lines():
    if line:
        line = line.decode("utf-8")
        if line.startswith("data: "):
            data = line[6:]
            if data == "[DONE]":
                break
            try:
                import json as _json
                chunk = _json.loads(data)
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")
            except Exception:
                continue
```

The official SDK's streaming client handles:
- Proper event type filtering (`message_start`, `content_block_start`, `content_block_delta`, `message_delta`)
- Error handling for malformed chunks
- `billed_tokens` reporting
- Automatic reconnection

The raw implementation only yields text chunks and silently swallows all errors.

**Severity**: MEDIUM — streaming works but is fragile.

### Action Item
- [ ] Replace with official SDK streaming: `client.messages.stream()`
- [ ] Handle `message_stop` event properly
- [ ] Report streaming metrics (time-to-first-token, total tokens)

---

## 5. Prompt Caching Not Implemented

### Finding: No `cache_control` Usage

The skill's **Prompt Caching** section says: *"For placement patterns, architectural guidance, and the silent-invalidator audit checklist: read `shared/prompt-caching.md`."*

NRG's prompts include:
- System prompt (schema hints, RBAC policies, DPDP rules) — stable across requests
- User query — varies per request
- Conversation history — grows per session

**For NRG's use case**, the system prompt (which includes schema hints from `schema_hints.md`) is the same for every SQL generation request. This is a perfect candidate for prompt caching.

**Severity**: HIGH — significant cost/latency savings available.

### Action Item
- [ ] Implement prompt caching with `cache_control: {type: "ephemeral"}` on system prompt
- [ ] Verify with `usage.cache_read_input_tokens` metric
- [ ] Check for silent invalidators (varying timestamps, unsorted JSON in system prompt)

---

## 6. `max_tokens: 800` Is Too Low for Complex Tasks

### Finding: Hard-Coded 800 Token Cap

```python
# llm_config.py:390 (non-streaming), line 436 (streaming)
"max_tokens": 800,
```

For complex synthesis tasks generating research responses, 800 tokens is very limiting. The skill says: *"Don't lowball `max_tokens` — hitting the cap truncates output mid-thought."*

For streaming responses (where `max_tokens` is used for the cap), the skill recommends `~64000` for streaming.

**Severity**: MEDIUM — responses may be truncated for complex queries.

### Action Item
- [ ] Increase `max_tokens` to 4096 for non-streaming synthesis tasks
- [ ] For streaming: use `max_tokens: 64000` (the SDK handles HTTP timeouts properly for streaming)

---

## 7. Conversation History Limited to 3 Turns

### Finding: Only Last 3 Turns Included

```python
# llm_config.py:380-386 (AnthropicMessagesClient)
for turn in conversation_history[-3:]:  # only last 3 turns
    if turn.get("query"):
        messages.append({"role": "user", "content": turn["query"]})
    if turn.get("response"):
        messages.append({"role": "assistant", "content": turn["response"]})
```

The skill's **Compaction** section says: *"For long-running conversations that may exceed the 1M context window, enable server-side compaction."*

With 382,653 audit events and a growing conversation history, the conversation history could eventually exceed the context window. The compaction feature requires the `compact-2026-01-12` beta header and proper handling of `content_block_delta` events.

**Severity**: LOW for now (3 turns × ~1000 tokens = ~3000 tokens, well within context), but will become an issue as sessions grow.

### Action Item
- [ ] Monitor conversation history length per session
- [ ] Implement compaction when history approaches 150K tokens
- [ ] Add `beta: {"compact-2026-01-12": true}` header when compaction is needed

---

## 8. Other LLM Providers: Same Issues

The other LLM clients (`NvidiaLLMClient`, `OpenAIResponsesClient`, `MinimaxLLMClient`, `AzureOpenAIClient`, `GeminiGenAIClient`) all share the same patterns:
- All use raw `requests` instead of official SDKs
- All hard-code `max_tokens: 800`
- All limit history to last 3 turns
- All lack streaming-specific optimizations

**Severity**: Same issues as Anthropic — MEDIUM overall.

---

## Positive Findings

### ✅ Excellent: `SovereignLLMMesh` Architecture
The `SovereignLLMMesh` (llm_config.py:700-1196) is **exceptionally well-designed**:
- Health-weighted provider selection: `1 / (latency_p95 × (1 + error_rate))`
- Circuit breaker with exponential backoff: 30s → 60s → 120s → 300s
- Parallel provider racing: top-2 (or top-3 for complex)
- Local SLM fallback
- Redis-backed circuit state for distributed deployment
- Auto-disable providers with >15% 7-day error rate

This is a **production-grade** mesh architecture that exceeds most commercial implementations.

### ✅ Excellent: `CostGuard` Budget Governance
The `CostGuard` class (llm_config.py:1209) with per-query caps, monthly thresholds, and persona-based routing is **excellent**:
- Per-query caps: trivial=₹0, simple=₹5, standard=₹50, complex=₹200, critical=₹500
- Monthly thresholds: warning 70%, critical 85%, halt 95%
- Tier-based routing: government → Indian providers, industry → cheapest path
- Redis-backed spend tracking

### ✅ Excellent: `LLMProviderError` with Budget Exhaustion Message
```python
raise LLMProviderError(
    f"LLM timeout budget exhausted ({self.mesh_config.query_timeout_budget_seconds}s). "
    f"Last error: {last_error}"
)
```
Clear, actionable error message with context.

---

## Summary Table

| Issue | Severity | File | Finding |
|-------|----------|------|---------|
| Raw `requests` instead of official SDK | MEDIUM | `llm_config.py:370-471` | No auto-retry, no SDK error classes |
| Outdated model `claude-3-5-sonnet-latest` | MEDIUM | `llm_config.py:132` | Should be `claude-sonnet-4-6` or `claude-opus-4-7` |
| No adaptive thinking | MEDIUM | `llm_config.py:388-393` | `thinking: {type: "adaptive"}` not used |
| Raw SSE parsing for streaming | MEDIUM | `llm_config.py:419-470` | Fragile custom parser instead of SDK streaming |
| No prompt caching | HIGH | `llm_config.py:388-393` | System prompt re-sent every request |
| `max_tokens: 800` too low | MEDIUM | `llm_config.py:390,436` | Responses truncated for complex tasks |
| History limited to 3 turns | LOW | `llm_config.py:380-386` | OK now, will matter with long sessions |

---

## Top 3 Priority Fixes

1. **HIGH IMPACT / LOW EFFORT**: Implement prompt caching — add `cache_control: {type: "ephemeral"}` to system prompt in Anthropic payload. This will reduce cost and latency for every SQL/synthesis request.

2. **MEDIUM IMPACT / MEDIUM EFFORT**: Migrate to official `anthropic` SDK — replace raw `requests` with `client.messages.create()` and `client.messages.stream()`. Gets auto-retry, proper error classes, and SDK streaming for free.

3. **MEDIUM IMPACT / LOW EFFORT**: Update default model to `claude-sonnet-4-6` and add `thinking: {type: "adaptive"}` to all Anthropic payloads.

---

## References

- Claude API Skill: `.claude/skills/claude-api/SKILL.md`
- Prompt Caching: `.claude/skills/claude-api/shared/prompt-caching.md` (referenced)
- Model Migration: `.claude/skills/claude-api/shared/model-migration.md` (referenced)
- Anthropic SDK: `pip install anthropic`

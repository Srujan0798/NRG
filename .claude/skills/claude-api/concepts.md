# Agent Design Patterns

This file covers decision heuristics for building agents on the Claude API: which primitives to reach for, how to design your tool surface, and how to manage context and cost over long runs. For per-tool mechanics and code examples, see `tool-use-concepts.md` and the language-specific folders.

---

## Model Parameters

| Parameter | When to use it | What to expect |
| --- | --- | --- |
| **Adaptive thinking** (`thinking: {type: "adaptive"}`) | When you want Claude to control when and how much to think. | Claude determines thinking depth per request and automatically interleaves thinking between tool calls. No token budget to tune. |
| **Effort** (`output_config: {effort: ...}`) | When adjusting the tradeoff between thoroughness and token efficiency. | Lower effort → fewer and more-consolidated tool calls, less preamble, terser confirmations. `medium` is often a favorable balance. Use `max` when correctness matters more than cost. |

See `SKILL.md` §Thinking & Effort for model support and parameter details.

---

## Designing Your Tool Surface

### Bash vs. dedicated tools

Claude doesn't know your application's security boundary, approval policy, or UX surface. Claude emits tool calls; your harness handles them. The shape of those tool calls determines what the harness can do.

A **bash tool** gives Claude broad programmatic leverage — it can perform almost any action. But it gives the harness only an opaque command string, the same shape for every action. Promoting an action to a **dedicated tool** gives the harness an action-specific hook with typed arguments it can intercept, gate, render, or audit.

**When to promote an action to a dedicated tool:**

- **Security boundary.** Actions that require gating are natural candidates. Reversibility is a useful criterion: hard-to-reverse actions (external API calls, sending messages, deleting data) can be gated behind user confirmation. A `send_email` tool is easy to gate; `bash -c "curl -X POST ..."` is not.
- **Staleness checks.** A dedicated `edit` tool can reject writes if the file changed since Claude last read it. Bash can't enforce that invariant.
- **Rendering.** Some actions benefit from custom UI. Claude Code promotes question-asking to a tool so it can render as a modal, present options, and block the agent loop until answered.
- **Scheduling.** Read-only tools like `glob` and `grep` can be marked parallel-safe. When the same actions run through bash, the harness can't tell a parallel-safe `grep` from a parallel-unsafe `git push`, so it must serialize.

**Rule of thumb:** Start with bash for breadth. Promote to dedicated tools when you need to gate, render, audit, or parallelize the action.

---

## Anthropic-Provided Tools

| Tool | Side | When to use it | What to expect |
| --- | --- | --- | --- |
| **Bash** | Client | Claude needs to execute shell commands. | Claude emits commands; your harness executes them. Reference implementation provided. |
| **Text editor** | Client | Claude needs to read or edit files. | Claude views, creates, and edits files via your implementation. Reference implementation provided. |
| **Computer use** | Client or Server | Claude needs to interact with GUIs, web apps, or visual interfaces. | Claude takes screenshots and issues mouse/keyboard commands. Can be self-hosted (you run the environment) or Anthropic-hosted. |
| **Code execution** | Server | Claude needs to run code in a isolated environment you don't want to manage. | Anthropic-hosted container with built-in file and bash sub-tools. No client-side execution. |
| **Web search / fetch** | Server | Claude needs information past its training cutoff (news, current events, recent docs) or the content of a specific URL. | Claude issues a query or URL; Anthropic executes it and returns results with citations. |
| **Memory** | Client | Claude needs to save context across sessions. | Claude reads/writes a `/memories` directory. You implement the storage backend. |

**Client-side** tools are defined by Anthropic (name, schema, Claude's usage pattern) but executed by your harness. Anthropic provides reference implementations. **Server-side** tools run entirely on Anthropic infrastructure — declare them in `tools` and Claude handles the rest.

---

## Composing Tool Calls: Programmatic Tool Calling

With standard tool use, each tool call is a round trip: Claude calls the tool, the result lands in Claude's context, Claude reasons about it, then calls the next tool. Three sequential actions (read profile → look up orders → check inventory) means three round trips. Each adds latency and tokens, and most of the intermediate data is never needed again.

**Programmatic tool calling (PTC)** lets Claude compose those calls into a script instead. The script runs in the code execution container. When the script calls a tool, the container pauses, the call is executed (client-side or server-side), and the result returns to the running code — not to Claude's context. The script processes it with normal control flow (loops, filters, branches). Only the script's final output returns to Claude.

| When to use it | What to expect |
| --- | --- |
| Many sequential tool calls, or large intermediate results you want filtered before they hit the context window. | Claude writes code that invokes tools as functions. Runs in the code execution container. Token cost scales with final output, not intermediate results. |

---

## Scaling the Tool and Instruction Set

| Feature | When to use it | What to expect |
| --- | --- | --- |
| **Tool search** | Many tools available, but only a few relevant per request. Don't want all schemas in context upfront. | Claude searches the tool set and loads only relevant schemas. Tool definitions are appended, not swapped — preserves cache (see Caching below). |
| **Skills** | Task-specific instructions Claude should load only when relevant. | Each skill is a folder with a `SKILL.md`. The skill's description sits in context by default; Claude reads the full file when the task calls for it. |

Both patterns keep the fixed context small and load detail on demand.

---

## Long-Running Agents: Managing Context

| Pattern | When to use it | What to expect |
| --- | --- | --- |
| **Context editing** | Context grows stale over many turns (old tool results, completed thinking). | Tool results and thinking blocks are cleared based on configurable thresholds. Keeps the transcript lean without summarizing. |
| **Compaction** | Conversation likely to reach or exceed the context window limit. | Earlier context is summarized into a compaction block server-side. See `SKILL.md` §Compaction for the critical `response.content` handling. |
| **Memory** | State must persist across sessions (not just within one conversation). | Claude reads/writes files in a memory directory. Survives process restarts. |

**Choosing between them:** Context editing and compaction operate within a session — editing prunes stale turns, compaction summarizes when you're near the limit. Memory is for cross-session persistence. Many long-running agents use all three.

---

## Caching for Agents

**Read `prompt-caching.md` first.** It covers the prefix-match invariant, breakpoint placement, the silent-invalidator audit, and why changing tools or models mid-session breaks the cache. This section covers only the agent-specific workarounds for those constraints.

| Constraint (from `prompt-caching.md`) | Agent-specific workaround |
| --- | --- |
| Editing the system prompt mid-session invalidates the cache. | Append a `<system-reminder>` block in the `messages` array instead. The cached prefix stays intact. Claude Code uses this for time updates and mode transitions. |
| Switching models mid-session invalidates the cache. | Spawn a **subagent** with the cheaper model for the sub-task; keep the main loop on one model. Claude Code's Explore subagents use Haiku this way. |
| Adding/removing tools mid-session invalidates the cache. | Use **tool search** for dynamic discovery — it appends tool schemas rather than swapping them, so the existing prefix is preserved. |

For multi-turn breakpoint placement, use top-level auto-caching — see `prompt-caching.md` §Placement patterns.

---

For live documentation on any of these features, see `live-sources.md`.
# Model Migration Guide

How to move existing code to newer Claude models. Covers breaking changes, deprecated parameters, and drop-in replacements for retired models.

For the latest, authoritative version (with code samples in every supported language), WebFetch the **Migration Guide** URL from `shared/live-sources.md`. Use this file for the consolidated, skill-resident reference; fall back to the live docs whenever a model launch or breaking change may have shifted the picture.

**This file is large.** Use the section names below to jump (or `Grep` this file for the heading text). Read Step 0 and Step 1 first — they apply to every migration. Then read only the per-target section for the model you are migrating to.

| Section | When you need it |
|---|---|
| Step 0: Confirm the migration scope | Always — before any edits |
| Step 1: Classify each file | Always — decides whether to swap, add-alongside, or skip |
| Per-SDK Syntax Reference | Translate the Python examples in this guide to TypeScript / Go / Ruby / Java / C# / PHP |
| Destination Models / Retired Model Replacements | Picking a target model |
| Breaking Changes by Source Model | Migrating to Opus 4.6 / Sonnet 4.6 |
| Migrating to Opus 4.7 | Migrating to Opus 4.7 (breaking changes, silent defaults, behavioral shifts) |
| Opus 4.7 Migration Checklist | The required vs optional items for 4.7, tagged `[BLOCKS]` / `[TUNE]` |
| Verify the Migration | After edits — runtime spot-check |

**TL;DR:** Change the model ID string. If you were using `budget_tokens`, switch to `thinking: {type: "adaptive"}`. If you were using assistant prefills, they 400 on both Opus 4.6 and Sonnet 4.6 — switch to one of the prefill replacements (most often `output_config.format`; see the table in Breaking Changes by Source Model). If you're moving from Sonnet 4.5 to Sonnet 4.6, set `effort` explicitly — 4.6 defaults to `high`. Remove the `effort-2025-11-24` and `fine-grained-tool-streaming-2025-05-14` beta headers (GA on 4.6); remove `interleaved-thinking-2025-05-14` once you're on adaptive thinking (keep it only while using the transitional `budget_tokens` escape hatch). Then drop back from `client.beta.messages.create` to `client.messages.create`. Dial back any aggressive "CRITICAL: YOU MUST" tool instructions; 4.6 follows the system prompt much more closely.

---

## Step 0: Confirm the migration scope

**Before any Write, Edit, or MultiEdit call, confirm the scope.** If the user's request does not explicitly name a single file, a specific directory, or an explicit file list, **ask first — do not start editing**. This is non-negotiable: even imperative-sounding requests like "migrate my codebase", "move my project to X", "upgrade to Sonnet 4.6", or bare "migrate to Opus 4.7" leave the scope ambiguous and require a clarifying question. Phrases like "my project", "my code", "my codebase", "the whole thing", "everywhere", or "across the repo" are **ambiguous, not directive** — they tell you *what* to do but not *where*. Ask before doing.

Offer the common scopes explicitly and wait for the answer before touching any file:

1. The entire working directory
2. A specific subdirectory (e.g. `src/`, `app/`, `services/billing/`)
3. A specific file or a list of files

Surface this as a single clarifying question so the user can answer in one turn. **Proceed without asking only when the scope is already unambiguous** — the user named an exact file ("migrate `extract.py` to Sonnet 4.6"), pointed at a specific directory ("migrate everything under `services/billing/` to Opus 4.6"), listed specific files ("update `a.py` and `b.py`"), or already answered the scope question in an earlier turn. If you can answer the question "which files is this change going to touch?" with a precise list from the prompt alone, proceed. If not, ask.

**Worked example.** If the user says *"Move my project to Opus 4.6. I want adaptive thinking everywhere it makes sense."* you do not know whether "my project" means the whole working directory, just `src/`, just the production code, or something else — the `everywhere` makes the intent clear (update every call site *within scope*) but the scope itself is still not defined. Do not start editing. Respond with:

> Before I start editing, can you confirm the scope? I can migrate:
> 1. Every `.py` file in the working directory
> 2. Just the files under `src/` (production code)
> 3. A specific subdirectory or list of files you name
>
> Which one?

Then wait for the answer. The same applies to *"Migrate to Opus 4.7"* and bare *"Help me upgrade to Sonnet 4.6"* — ask before editing.

**Sizing the scope question (large repos).** Before asking, get a per-directory count so the user can pick concretely:

```sh
rg -l "<old-model-id>" --type-not md | cut -d/ -f1 | sort | uniq -c | sort -rn
```

Present the breakdown in your scope question (e.g. *"Found 217 references across 3 directories: api/ (130), api-go/ (62), routing/ (25). Which to migrate?"*). Also confirm `git status` is clean before surveying — unexpected modifications mean a concurrent process; stop and investigate before proceeding.

---

## Step 1: Classify each file

Not every file that contains the old model ID is a **caller** of the API. Before editing, classify each file into one of these buckets — the right action differs:

| # | Bucket | What it looks like | Action |
|---|---|---|---|
| 1 | **Calls the API/SDK** | `client.messages.create(model=…)`, `anthropic.Anthropic()`, request payloads | Swap the model ID **and** apply the breaking-change checklist for the target version (below). |
| 2 | **Defines or serves the model** | Model registries, OpenAPI specs, routing/queue configs, model-policy enums, generated catalogs | The old entry **stays** (the model is still served). Ask whether to (a) add the new model alongside, (b) leave alone, or (c) retire the old model — never blind-replace. **If you can't ask, default to (a): add the new model alongside and flag it** — replacing would de-register a model that's still in production. |
| 3 | **References the ID as an opaque string** | UI fallback constants, capability-gate substring checks, generic test fixtures, label parsers, env defaults | Usually swap the string and verify any parser/regex/substring match handles the new ID — but check the sub-cases below first. |
| 4 | **Suffixed variant ID** | `claude-<model>-<suffix>` like `-fast`, `-1024k`, `-200k`, `[1m]`, dated snapshots | These are deployment/routing identifiers, not the public model ID. **Do not assume a new-model equivalent exists.** Verify in the registry first; if absent, leave the string alone and flag it. |

**Bucket 3 sub-cases — before swapping a string reference, check:**

- **Capability gate** (e.g. `if 'opus-4-6' in model_id:` enables a feature) → **add the new ID alongside**, don't replace. The old model is still served and still has the capability, so replacing would silently disable the feature for any old-model traffic that still flows through. If you know no old-model traffic will hit this gate (single-caller codebase fully migrating), replacing is fine; if unsure, add alongside.
- **Registry-assert test** (e.g. `assert "claude-X" in supported_models`, `test_X_has_N_clusters`) → **add an assertion for the new model alongside; keep the old one.** The old model is still served, so its assertion stays valid — but the registry should also include the new model, so assert that too. Heuristic: if the test references multiple model versions in a list, it's a registry test; if one model in a struct compared only to itself, it's a generic fixture.
- **Frozen / generated snapshot** → **regenerate**, don't hand-edit.
- **Coupled to a definer** (e.g. an integration test that passes model authorization via a shared `conftest` seed list, or asserts on a billing-tier / rate-limit-group enum or a generated SKU/pricing catalog) → **verify the definer has a new-model entry first.** If not, add a seed entry (reusing the nearest existing tier as a placeholder); if you can't confidently do that, ask the user how to populate the definer. **Do not skip the test.** Swapping without populating the definer will make the test fail at runtime.

When migrating tests specifically: breaking parameters (`temperature`, `top_p`, `budget_tokens`) are usually absent — test fixtures rarely set sampling params on placeholder models. The breaking-change scan is still required, but expect mostly clean results.

**Find intentionally-flagged sync points first.** Many codebases tag spots that must change at every model launch with comment markers like `MODEL LAUNCH`, `KEEP IN SYNC`, `@model-update`, or similar. Grep for whatever convention the repo uses *before* the broad model-ID grep — those markers point at the load-bearing changes.

---

## Per-SDK Syntax Reference

Code examples in this guide are Python. **The same fields exist in every official Anthropic SDK** — Stainless generates all 7 from the same OpenAPI spec, so JSON field names map 1:1 with only case-convention differences. Use the rows below to translate the Python examples to the SDK you are migrating.

> **Verify type and method names against the SDK source before writing them into customer code.** WebFetch the relevant repository from the SDK source-code table in `shared/live-sources.md` (one row per SDK) and confirm the exact symbol — particularly for typed SDKs (Go, Java, C#) where union/builder names can differ from the JSON shape. Do not guess type names that aren't in the table below or in `<lang>/claude-api/README.md`.


### `thinking` — `budget_tokens` → adaptive

| SDK | Before | After |
|---|---|---|
| Python | `thinking={"type": "enabled", "budget_tokens": N}` | `thinking={"type": "adaptive"}` |
| TypeScript | `thinking: { type: 'enabled', budget_tokens: N }` | `thinking: { type: 'adaptive' }` |
| Go | `Thinking: anthropic.ThinkingConfigParamOfEnabled(N)` | `Thinking: anthropic.ThinkingConfigParamUnion{OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{}}` |
| Ruby | `thinking: { type: "enabled", budget_tokens: N }` | `thinking: { type: "adaptive" }` |
| Java | `.thinking(ThinkingConfigEnabled.builder().budgetTokens(N).build())` | `.thinking(ThinkingConfigAdaptive.builder().build())` |
| C# | `Thinking = new ThinkingConfigEnabled { BudgetTokens = N }` | `Thinking = new ThinkingConfigAdaptive()` |
| PHP | `thinking: ['type' => 'enabled', 'budget_tokens' => N]` | `thinking: ['type' => 'adaptive']` |

### Sampling parameters — `temperature` / `top_p` / `top_k`

(Remove the field entirely on Opus 4.7; on Claude 4.x keep at most one of `temperature` or `top_p`.)

| SDK | Field(s) to remove |
|---|---|
| Python | `temperature=…`, `top_p=…`, `top_k=…` |
| TypeScript | `temperature: …`, `top_p: …`, `top_k: …` |
| Go | `Temperature: anthropic.Float(…)`, `TopP: anthropic.Float(…)`, `TopK: anthropic.Int(…)` |
| Ruby | `temperature: …`, `top_p: …`, `top_k: …` |
| Java | `.temperature(…)`, `.topP(…)`, `.topK(…)` |
| C# | `Temperature = …`, `TopP = …`, `TopK = …` |
| PHP | `temperature: …`, `topP: …`, `topK: …` |

### Prefill replacement — structured outputs via `output_config.format`

| SDK | Remove (last assistant turn) | Add |
|---|---|---|
| Python | `{"role": "assistant", "content": "…"}` | `output_config={"format": {"type": "json_schema", "schema": SCHEMA}}` |
| TypeScript | `{ role: 'assistant', content: '…' }` | `output_config: { format: { type: 'json_schema', schema: SCHEMA } }` |
| Go | trailing `anthropic.MessageParam{Role: "assistant", …}` | `OutputConfig: anthropic.OutputConfigParam{Format: anthropic.JSONOutputFormatParam{…}}` |
| Ruby | `{ role: "assistant", content: "…" }` | `output_config: { format: { type: "json_schema", schema: SCHEMA } }` |
| Java | trailing `Message.builder().role(ASSISTANT)…` | `.outputConfig(OutputConfig.builder().format(JsonOutputFormat.builder()…build()).build())` |
| C# | trailing `new Message { Role = "assistant", … }` | `OutputConfig = new OutputConfig { Format = new JsonOutputFormat { … } }` |
| PHP | trailing `['role' => 'assistant', 'content' => '…']` | `outputConfig: ['format' => ['type' => 'json_schema', 'schema' => $SCHEMA]]` |

### `thinking.display` — opt back into summarized reasoning (Opus 4.7)

| SDK | Add |
|---|---|
| Python | `thinking={"type": "adaptive", "display": "summarized"}` |
| TypeScript | `thinking: { type: 'adaptive', display: 'summarized' }` |
| Go | `Thinking: anthropic.ThinkingConfigParamUnion{OfAdaptive: &anthropic.ThinkingConfigAdaptiveParam{Display: anthropic.ThinkingConfigAdaptiveDisplaySummarized}}` |
| Ruby | `thinking: { type: "adaptive", display: "summarized" }` (or `display_:` when constructing the model class directly) |
| Java | `.thinking(ThinkingConfigAdaptive.builder().display(ThinkingConfigAdaptive.Display.SUMMARIZED).build())` |
| C# | `Thinking = new ThinkingConfigAdaptive { Display = Display.Summarized }` |
| PHP | `thinking: ['type' => 'adaptive', 'display' => 'summarized']` |

For any field not in these tables, the JSON key in the Python example translates directly: `snake_case` for Python/TypeScript/Ruby, `camelCase` named args for PHP, `PascalCase` struct fields for Go/C#, `camelCase` builder methods for Java.

---

## Explain every change you make

Migration edits often look arbitrary to a user who hasn't read the release notes — a removed `temperature`, a deleted prefill, a rewritten system-prompt sentence. **For each edit, tell the user what you changed and why**, tied to the specific API or behavioral change that motivates it. Do this in your summary as you work, not just at the end.

Be especially explicit about **system-prompt edits**. Users are rightly protective of their prompts, and prompt-tuning changes are judgment calls (not hard API requirements). For any prompt edit:

- Quote the before and after text.
- State the behavioral shift that motivates it (e.g. *"Opus 4.7 calibrates response length to task complexity, so I added an explicit length instruction"*, or *"4.6 follows instructions more literally, so 'CRITICAL: YOU MUST use the search tool' will now overtrigger — softened to 'Use the search tool when…'"*).
- Make clear which prompt edits are **optional tuning** (tone, length, subagent guidance) versus which code edits are **required to avoid a 400** (sampling params, `budget_tokens`, prefills). Never present an optional prompt change as mandatory.

If you're applying several prompt-tuning edits at once, offer them as a short list the user can accept or decline item-by-item rather than silently rewriting their system prompt.

---

## Before You Migrate

1. **Confirm the target model ID.** Use only the exact strings from `shared/models.md` — do not append date suffixes to aliases (`claude-opus-4-6`, not `claude-opus-4-6-20251101`). Guessing an ID will 404.
2. **Check which features your code uses** with this checklist:
   - `thinking: {type: "enabled", budget_tokens: N}` → migrate to adaptive thinking on Opus 4.6 / Sonnet 4.6 (still functional but deprecated)
   - Assistant-turn prefills (`messages` ending with `role: "assistant"`) → must change on Opus 4.6 / Sonnet 4.6 (returns 400)
   - `output_format` parameter on `messages.create()` → must change on all models (deprecated API-wide)
   - `max_tokens > ~16000` → must stream on any model (above ~16K risks SDK HTTP timeouts). When streaming, Sonnet 4.6 / Haiku 4.5 cap at 64K and Opus 4.6 caps at 128K
   - Beta headers `effort-2025-11-24`, `fine-grained-tool-streaming-2025-05-14`, `interleaved-thinking-2025-05-14` → GA on 4.6, remove them and switch from `client.beta.messages.create` to `client.messages.create`
   - Moving Sonnet 4.5 → Sonnet 4.6 with no `effort` set → 4.6 defaults to `high`, which may change your latency/cost profile
   - System prompts with `CRITICAL`, `MUST`, `If in doubt, use X` language → likely to overtrigger on 4.6 (see Prompt-Behavior Changes)
   - Coming from 3.x / 4.0 / 4.1: also check sampling params (`temperature` + `top_p`), tool versions (`text_editor_20250728`), `refusal` + `model_context_window_exceeded` stop reasons, trailing-newline tool-param handling
3. **Test on a single request first.** Run one call against the new model, inspect the response, then roll out.

---

## Destination Models (recommended targets)

| If you're on…                         | Migrate to         | Why                                               |
| ------------------------------------- | ------------------ | ------------------------------------------------- |
| Opus 4.6                              | `claude-opus-4-7`  | Most capable model; adaptive thinking only; high-res vision; see Migrating to Opus 4.7 |
| Opus 4.0 / 4.1 / 4.5 / Opus 3         | `claude-opus-4-6`  | Most intelligent 4.x before 4.7; adaptive thinking; 128K output |
| Sonnet 4.0 / 4.5 / 3.7 / 3.5          | `claude-sonnet-4-6`| Best speed / intelligence balance; adaptive thinking; 64K output |
| Haiku 3 / 3.5                         | `claude-haiku-4-5` | Fastest and most cost-effective                   |

Default to the latest Opus for the caller's tier unless they explicitly chose otherwise. If you're moving from Opus 4.5 or older directly to Opus 4.7, apply the 4.6 migration first, then layer the Opus 4.7 changes on top (see Migrating to Opus 4.7 below).

---

## Retired Model Replacements

These models return 404 — update immediately:

| Retired model                 | Retired       | Drop-in replacement  |
| ----------------------------- | ------------- | -------------------- |
| `claude-3-7-sonnet-20250219`  | Feb 19, 2026  | `claude-sonnet-4-6`  |
| `claude-3-5-haiku-20241022`   | Feb 19, 2026  | `claude-haiku-4-5`   |
| `claude-3-opus-20240229`      | Jan 5, 2026   | `claude-opus-4-7`    |
| `claude-3-5-sonnet-20241022`  | Oct 28, 2025  | `claude-sonnet-4-6`  |
| `claude-3-5-sonnet-20240620`  | Oct 28, 2025  | `claude-sonnet-4-6`  |
| `claude-3-sonnet-20240229`    | Jul 21, 2025  | `claude-sonnet-4-6`  |
| `claude-2.1`, `claude-2.0`    | Jul 21, 2025  | `claude-sonnet-4-6`  |

## Deprecated Models (retiring soon)

| Model                         | Retires       | Replacement          |
| ----------------------------- | ------------- | -------------------- |
| `claude-3-haiku-20240307`     | Apr 19, 2026  | `claude-haiku-4-5`   |
| `claude-opus-4-20250514`      | June 15, 2026 | `claude-opus-4-7`    |
| `claude-sonnet-4-20250514`    | June 15, 2026 | `claude-sonnet-4-6`  |

---

## Breaking Changes by Source Model

### Migrating from Sonnet 4.5 to Sonnet 4.6 (effort default change)

Sonnet 4.5 had no `effort` parameter; Sonnet 4.6 defaults to `high`. If you just switch the model string and do nothing else, you may see noticeably higher latency and token usage. Set `effort` explicitly.

**Recommended starting points:**

| Workload                                          | Start at       | Notes                                                                                                    |
| ------------------------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------- |
| Chat, classification, content generation          | `low`          | With `thinking: {"type": "disabled"}` you'll see similar or better performance vs. Sonnet 4.5 no-thinking |
| Most applications (balanced)                      | `medium`       | The default sweet spot for quality vs. cost                                                              |
| Agentic coding, tool-heavy workflows              | `medium`       | Pair with adaptive thinking and a generous `max_tokens` (up to 64K with streaming — Sonnet 4.6's ceiling) |
| Autonomous multi-step agents, long-horizon loops  | `high`         | Scale down to `medium` if latency/tokens become a concern                                                 |
| Computer-use agents                               | `high` + adaptive | Sonnet 4.6's best computer-use accuracy is on adaptive + high                                          |

For non-thinking chat workloads specifically:

```python
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=8192,
    thinking={"type": "disabled"},
    output_config={"effort": "low"},
    messages=[{"role": "user", "content": "..."}],
)
```

**When to use Opus 4.6 instead:** hardest and longest-horizon problems — large code migrations, deep research, extended autonomous work. Sonnet 4.6 wins on fast turnaround and cost efficiency.

### Migrating to Opus 4.6 / Sonnet 4.6 (from any older model)

**1. Manual extended thinking is deprecated — use adaptive thinking.**

`thinking: {type: "enabled", budget_tokens: N}` (manual extended thinking with a fixed token budget) is deprecated on Opus 4.6 and Sonnet 4.6. Replace it with `thinking: {type: "adaptive"}`, which lets Claude decide when and how much to think. Adaptive thinking also enables interleaved thinking automatically (no beta header needed).

```python
# Old (still works on older models, deprecated on 4.6)
response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=16000,
    thinking={"type": "enabled", "budget_tokens": 8000},
    messages=[...]
)

# New (Opus 4.6 / Sonnet 4.6)
response = client.messages.create(
    model="claude-opus-4-6",  # or "claude-sonnet-4-6"
    max_tokens=16000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # optional: low | medium | high | max
    messages=[...]
)
```

Adaptive thinking is the long-term target, and on internal evaluations it outperforms manual extended thinking. Move when you can.

**Transitional escape hatch:** manual extended thinking is still *functional* on Opus 4.6 and Sonnet 4.6 (deprecated, will be removed in a future release). If you need a hard ceiling while migrating — for example, to bound token spend on a runaway workload before you've tuned `effort` — you can keep `budget_tokens` around alongside an explicit `effort` value, then remove it in a follow-up. `budget_tokens` must be strictly less than `max_tokens`:

```python
# Transitional only — deprecated, plan to remove
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16384,
    thinking={"type": "enabled", "budget_tokens": 8192},  # must be < max_tokens
    output_config={"effort": "medium"},
    messages=[...],
)
```

If the user asks for a "thinking budget" on 4.6, the preferred answer is `effort` — use `low`, `medium`, `high`, or `max` (Opus-tier only — not Sonnet or Haiku) rather than a token count.

**2. Effort parameter (Opus 4.5, Opus 4.6, Sonnet 4.6 only).**

Controls thinking depth and overall token spend. Goes inside `output_config`, not top-level. Default is `high`. `max` is Opus-tier only (Opus 4.6 and later — not Sonnet or Haiku). Errors on Sonnet 4.5 and Haiku 4.5.

```python
output_config={"effort": "medium"}  # often the best cost / quality balance
```

### Migrating to the 4.6 family (Opus 4.6 and Sonnet 4.6)

**3. Assistant-turn prefills return 400 (Opus 4.6 and Sonnet 4.6).**

Prefilled responses on the final assistant turn are no longer supported on either Opus 4.6 or Sonnet 4.6 — both return a 400. Adding assistant messages *elsewhere* in the conversation (e.g., for few-shot examples) still works. Pick the replacement that matches what the prefill was doing:

| Prefill was used for                               | Replacement                                                                                                                               |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Forcing JSON / YAML / schema output                | `output_config.format` with a `json_schema` — see example below                                                                           |
| Forcing a classification label                     | Tool with an enum field containing valid labels, or structured outputs                                                                    |
| Skipping preambles (`Here is the summary:\n`)      | System prompt instruction: *"Respond directly without preamble. Do not start with phrases like 'Here is...' or 'Based on...'."*           |
| Steering around bad refusals                       | Usually no longer needed — 4.6 refuses far more appropriately. Plain user-turn prompting is sufficient.                                   |
| Continuing an interrupted response                 | Move continuation into the user turn: *"Your previous response was interrupted and ended with `[last text]`. Continue from there."*     |
| Injecting reminders / context hydration            | Inject into the user turn instead. For complex agent harnesses, expose context via a tool call or during compaction.                      |

```python
# Old (fails on Opus 4.6 / Sonnet 4.6) — prefill forcing JSON shape
messages=[
    {"role": "user", "content": "Extract the name."},
    {"role": "assistant", "content": "{\"name\": \""},
]

# New — structured outputs replace the prefill
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    output_config={"format": {"type": "json_schema", "schema": {...}}},
    messages=[{"role": "user", "content": "Extract the name."}],
)
```

**4. Stream for `max_tokens > ~16K` (all models); Opus 4.6 alone reaches 128K.**

Non-streaming requests hit SDK HTTP timeouts at high `max_tokens`, regardless of model — stream for anything above ~16K output. The streamable ceiling differs by model: Sonnet 4.6 and Haiku 4.5 cap at 64K, and Opus 4.6 alone goes up to 128K.

```python
with client.messages.stream(model="claude-opus-4-6", max_tokens=64000, ...) as stream:
    message = stream.get_final_message()
```

**5. Tool-call JSON escaping may differ (Opus 4.6 and Sonnet 4.6).**

Both 4.6 models can produce tool call `input` fields with Unicode or forward-slash escaping. Always parse with `json.loads()` / `JSON.parse()` — never raw-string-match the serialized input.

### All models

**6. `output_format` → `output_config.format` (API-wide).**

The old top-level `output_format` parameter on `messages.create()` is deprecated. Use `output_config.format` instead. This is not 4.6-specific — applies to every model.

---

## Beta Headers to Remove on 4.6

Several beta headers that were required on 4.5 are now GA on 4.6 and should be removed. Leaving them in is harmless but misleading; removing them also lets you move from `client.beta.messages.create(...)` back to `client.messages.create(...)`.

| Header                                    | Status on 4.6                                              | Action                                                  |
| ----------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------- |
| `effort-2025-11-24`                       | Effort parameter is GA                                     | Remove                                                  |
| `fine-grained-tool-streaming-2025-05-14`  | GA                                                         | Remove                                                  |
| `interleaved-thinking-2025-05-14`         | Adaptive thinking enables interleaved thinking automatically | Remove when using adaptive thinking; still functional on Sonnet 4.6 *with* manual extended thinking, but that path is deprecated |
| `token-efficient-tools-2025-02-19`        | Built in to all Claude 4+ models                           | Remove (no effect)                                      |
| `output-128k-2025-02-19`                  | Built in to Claude 4+ models                               | Remove (no effect)                                      |

Once you remove all of these and finish moving to adaptive thinking, you can switch the SDK call site from the beta namespace back to the regular one:

```python
# Before
response = client.beta.messages.create(
    model="claude-opus-4-5",
    betas=["interleaved-thinking-2025-05-14", "effort-2025-11-24"],
    ...
)

# After
response = client.messages.create(
    model="claude-opus-4-6",
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},
    ...
)
```

---

## Additional Changes When Coming from 3.x / 4.0 / 4.1 → 4.6

If you're jumping from Opus 4.1, Sonnet 4, Sonnet 3.7, or an older Claude 3.x model directly to 4.6, apply everything above *plus* the items in this section. Users already on Opus 4.5 / Sonnet 4.5 can skip this.

**1. Sampling parameters: `temperature` OR `top_p`, not both.**

Passing both will error on every Claude 4+ model:

```python
# Old (3.x only — errors on 4+)
client.messages.create(temperature=0.7, top_p=0.9, ...)

# New
client.messages.create(temperature=0.7, ...)  # or top_p, not both
```

**2. Update tool versions.**

Legacy tool versions are not supported on 4+. **Both the `type` and the `name` field change** — `text_editor_20250728` and `str_replace_based_edit_tool` are a pair; updating one without the other 400s. Also remove the `undo_edit` command from your text-editor integration:

| Old                                               | New                                                     |
| ------------------------------------------------- | ------------------------------------------------------- |
| `text_editor_20250124` + `str_replace_editor`     | `text_editor_20250728` + `str_replace_based_edit_tool`  |
| `code_execution_*` (earlier versions)             | `code_execution_20250825`                               |
| `undo_edit` command                               | *(no longer supported — delete call sites)*             |

```python
# Before
tools = [{"type": "text_editor_20250124", "name": "str_replace_editor"}]

# After — BOTH fields change
tools = [{"type": "text_editor_20250728", "name": "str_replace_based_edit_tool"}]
```

**3. Handle the `refusal` stop reason.**

Claude 4+ can return `stop_reason: "refusal"` on the response. If your code only handles `end_turn` / `tool_use` / `max_tokens`, add a branch:

```python
if response.stop_reason == "refusal":
    # Surface the refusal to the user; do not retry with the same prompt
    ...
```

**4. Handle the `model_context_window_exceeded` stop reason (4.5+).**

Distinct from `max_tokens`: it means the model hit the *context window* limit, not the requested output cap. Handle both:

```python
if response.stop_reason == "model_context_window_exceeded":
    # Context window exhausted — compact or split the conversation
    ...
elif response.stop_reason == "max_tokens":
    # Requested output cap hit — retry with higher max_tokens or stream
    ...
```

**5. Trailing newlines preserved in tool call string parameters (4.5+).**

4.5 and 4.6 preserve trailing newlines that older models stripped. If your tool implementations do exact string matching against tool-call `input` values (e.g., `if name == "foo"`), verify they still match when the model sends `"foo\n"`. Normalizing with `.rstrip()` on the receiving side is usually the simplest fix.

**6. Haiku: rate limits reset between generations.**

Haiku 4.5 has its own rate-limit pool separate from Haiku 3 / 3.5. If you're ramping traffic as you migrate, check your tier's Haiku 4.5 limits at [API rate limits](https://platform.claude.com/docs/en/api/rate-limits) — a quota that comfortably served Haiku 3.5 traffic may need a tier bump for the same volume on 4.5.

---

## Prompt-Behavior Changes (Opus 4.5 / 4.6, Sonnet 4.6)

These don't break your code, but prompts that worked on 4.5-and-earlier may over- or under-trigger on 4.6. Tune as needed.

**1. Aggressive instructions cause overtriggering.** Opus 4.5 and 4.6 follow the system prompt much more closely than earlier models. Prompts written to *overcome* the old reluctance are now too aggressive:

| Before (worked on 4.0 / 4.5)                | After (use on 4.6)                        |
| ------------------------------------------- | ----------------------------------------- |
| `CRITICAL: You MUST use this tool when...`  | `Use this tool when...`                   |
| `Default to using [tool]`                   | `Use [tool] when it would improve X`      |
| `If in doubt, use [tool]`                   | *(delete — no longer needed)*             |

If the model is now overtriggering a tool or skill, the fix is almost always to dial back the language, not to add more guardrails.

**2. Overthinking and excessive exploration (Opus 4.6).** At higher `effort` settings, Opus 4.6 explores more before answering. If that burns too many thinking tokens, lower `effort` first (`medium` is often the sweet spot) before adding prose instructions to constrain reasoning.

**3. Overeager subagent spawning (Opus 4.6).** Opus 4.6 has a strong preference for delegating to subagents. If you see it spawning a subagent for something a direct `grep` or `read` would solve, add guidance: *"Use subagents only for parallel or independent workstreams. For single-file reads or sequential operations, work directly."*

**4. Overengineering (Opus 4.5 / 4.6).** Both models may add extra files, abstractions, or defensive error handling beyond what was asked. If you want minimal changes, prompt for it explicitly: *"Only make changes directly requested. Don't add helpers, abstractions, or error handling for scenarios that can't happen."*

**5. LaTeX math output (Opus 4.6).** Opus 4.6 defaults to LaTeX (`\frac{}{}`, `$...$`) for math and technical content. If you need plain text, instruct it explicitly: *"Format all math as plain text — no LaTeX, no `$`, no `\frac{}{}`. Use `/` for division and `^` for exponents."*

**6. Skipped verbal summaries (4.6 family).** The 4.6 models are more concise and may skip the summary paragraph after a tool call, jumping straight to the next action. If you rely on those summaries for visibility, add: *"After completing a task that involves tool use, provide a brief summary of what you did."*

**7. "Think" as a trigger word (Opus 4.5 with thinking disabled).** When `thinking` is off, Opus 4.5 is particularly sensitive to the word *think* and may reason more than you want. Use `consider`, `evaluate`, or `reason through` instead.

---

## Model-ID Rename Quick Reference

| Old string (migration source)  | New string         |
| ------------------------------ | ------------------ |
| `claude-opus-4-6`              | `claude-opus-4-7`  |
| `claude-opus-4-5`              | `claude-opus-4-7`  |
| `claude-opus-4-1`              | `claude-opus-4-7`  |
| `claude-opus-4-0`              | `claude-opus-4-7`  |
| `claude-sonnet-4-5`            | `claude-sonnet-4-6`|
| `claude-sonnet-4-0`            | `claude-sonnet-4-6`|

Older aliases (`claude-opus-4-5`, `claude-sonnet-4-5`, `claude-opus-4-1`, etc.) are still active and can be pinned if you need time before upgrading — see `shared/models.md` for the full legacy list.

---

## Migration Checklist

Every item is tagged: **`[BLOCKS]`** items cause a 400 error, infinite loop, silent timeout, or wrong tool selection if missed — apply these as code edits, not as suggestions. **`[TUNE]`** items are quality/cost adjustments.

For each file that calls `messages.create()` / equivalent SDK method:

- [ ] **[BLOCKS]** Update the `model=` string to the new alias
- [ ] **[BLOCKS]** Replace `budget_tokens` with `thinking={"type": "adaptive"}` (deprecated on Opus 4.6 / Sonnet 4.6)
- [ ] **[BLOCKS]** Move `format` from top-level `output_format` into `output_config.format`
- [ ] **[BLOCKS]** Remove any assistant-turn prefills if targeting Opus 4.6 or Sonnet 4.6 (see the prefill replacement table)
- [ ] **[BLOCKS]** Switch to streaming if `max_tokens > ~16000` (otherwise SDK HTTP timeout)
- [ ] **[TUNE]** Set `output_config={"effort": "..."}` explicitly — especially when moving Sonnet 4.5 → Sonnet 4.6 (4.6 defaults to `high`)
- [ ] **[TUNE]** Remove GA beta headers: `effort-2025-11-24`, `fine-grained-tool-streaming-2025-05-14`, `token-efficient-tools-2025-02-19`, `output-128k-2025-02-19`; remove `interleaved-thinking-2025-05-14` once on adaptive thinking
- [ ] **[TUNE]** Switch `client.beta.messages.create(...)` → `client.messages.create(...)` once all betas are removed
- [ ] **[TUNE]** Review system prompt for aggressive tool language (`CRITICAL:`, `MUST`, `If in doubt`) and dial it back

**Extra items when coming from 3.x / 4.0 / 4.1:**
- [ ] **[BLOCKS]** Remove either `temperature` or `top_p` (passing both 400s on Claude 4+)
- [ ] **[BLOCKS]** Update text-editor tool `type` to `text_editor_20250728`
- [ ] **[BLOCKS]** Update text-editor tool `name` to `str_replace_based_edit_tool` — **changing only the `type` and keeping `name: "str_replace_editor"` returns a 400**
- [ ] **[BLOCKS]** Update code-execution tool to `code_execution_20250825`
- [ ] **[BLOCKS]** Delete any `undo_edit` command call sites
- [ ] **[TUNE]** Add handling for `stop_reason == "refusal"`
- [ ] **[TUNE]** Add handling for `stop_reason == "model_context_window_exceeded"` (4.5+)
- [ ] **[TUNE]** Verify tool-param string matching tolerates trailing newlines (preserved on 4.5+)
- [ ] **[TUNE]** If moving to Haiku 4.5: review rate-limit tier (separate pool from Haiku 3.x)

**Verification:**
- [ ] Run one test request and inspect `response.stop_reason`, `response.usage`, and whether tool-use / thinking behavior matches expectations

For cached prompts: the render order and hash inputs did not change, so existing `cache_control` breakpoints keep working. However, **changing the model string invalidates the existing cache** — the first request on the new model will write the cache fresh.

---

## Migrating to Opus 4.7

> **Model ID `claude-opus-4-7` is authoritative as written here.** When the user asks to migrate to Opus 4.7, write `model="claude-opus-4-7"` exactly. Do **not** WebFetch to verify — this guide is the source of truth for migration target IDs. The corresponding entry exists in `shared/models.md`.

Claude Opus 4.7 is our most capable generally available model to date. It is highly autonomous and performs exceptionally well on long-horizon agentic work, knowledge work, vision tasks, and memory tasks. This section summarizes everything new at launch. It is layered on top of the 4.6 migration above — if the caller is jumping from Opus 4.5 or older, apply the 4.6 changes first, then apply this section.

**TL;DR for someone already on Opus 4.6:** update the model ID to `claude-opus-4-7`, strip any remaining `budget_tokens` and sampling parameters (both 400 on Opus 4.7), give `max_tokens` extra headroom and re-baseline with `count_tokens()` against the new model, opt back into `thinking.display: "summarized"` if reasoning is surfaced to users, and re-tune `effort` — it matters more on 4.7 than on any prior Opus.

### Breaking changes (will 400 on Opus 4.7)

**Extended thinking removed.**

`thinking: {type: "enabled", budget_tokens: N}` is no longer supported on Claude Opus 4.7 or later models and returns a 400 error. Switch to adaptive thinking (`thinking: {type: "adaptive"}`) and use the effort parameter to control thinking depth. Adaptive thinking is **off by default** on Claude Opus 4.7: requests with no `thinking` field run without thinking, matching Opus 4.6 behavior. Set `thinking: {type: "adaptive"}` explicitly to enable it.

```python
# Before (Opus 4.6)
client.messages.create(
    model="claude-opus-4-6",
    max_tokens=64000,
    thinking={"type": "enabled", "budget_tokens": 32000},
    messages=[{"role": "user", "content": "..."}],
)

# After (Opus 4.7)
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # or "max", "xhigh", "medium", "low"
    messages=[{"role": "user", "content": "..."}],
)
```

If the caller wasn't using extended thinking, no change is required — thinking is off by default, or can be set explicitly with `thinking={"type": "disabled"}`.

Delete `budget_tokens` plumbing entirely. For the replacement `effort` value, see **Choosing an effort level on Opus 4.7** below — there is no exact 1:1 mapping from `budget_tokens`.

**Sampling parameters removed.**

The `temperature`, `top_p`, and `top_k` parameters are no longer accepted on Claude Opus 4.7. Requests that include them return a 400 error. Remove these fields from your request payloads. Prompting is the recommended way to guide model behavior on Claude Opus 4.7. If you were using `temperature = 0` for determinism, note that it never guaranteed identical outputs on prior models.

```python
# Before — errors on Opus 4.7
client.messages.create(temperature=0.7, top_p=0.9, ...)

# After
client.messages.create(...)  # no sampling params
```

- **If the intent was determinism** — use `effort: "low"` with a tighter prompt.
- **If the intent was creative variance** — the prompt replacement depends on the use case; **ask the user** how they want variance elicited. If you can't ask, add a use-case-appropriate instruction along the lines of *"choose something off-distribution and interesting"* — e.g. for text generation, *"Vary your phrasing and structure across responses"*; for frontend/design, use the propose-4-directions approach under **Design and frontend coding** below.

### Choosing an effort level on Opus 4.7

`budget_tokens` controlled how much to *think*; `effort` controls how much to think *and* act, so there is no exact 1:1 mapping. **Use `xhigh` for best results in coding and agentic use cases, and a minimum of `high` for most intelligence-sensitive use cases.** Experiment with other levels to further tune token usage and intelligence:

| Level | Use when | Notes |
| --- | --- | --- |
| `max` | Intelligence-demanding tasks worth testing at the ceiling | Can deliver gains in some use cases but may show diminishing returns from increased token usage; can be prone to overthinking |
| `xhigh` | **Most coding and agentic use cases** | The best setting for these; used as the default in Claude Code |
| `high` | Intelligence-sensitive use cases generally | Balances token usage and intelligence; recommended minimum for most intelligence-sensitive work |
| `medium` | Cost-sensitive use cases that need to reduce token usage while trading off intelligence | |
| `low` | Short, scoped tasks and latency-sensitive workloads that are not intelligence-sensitive | |

### Silent default changes (no error, but behavior differs)

**Thinking content omitted by default.**

Thinking blocks still appear in the response stream on Claude Opus 4.7, but their `thinking` field is empty unless you explicitly opt in. This is a silent change from Claude Opus 4.6, where the default was to return summarized thinking text. To restore summarized thinking content on Claude Opus 4.7, set `thinking.display` to `"summarized"`. **The block-field name is unchanged** — it is still `block.thinking` on a `thinking`-type block; do not rename it.

**Detect this:** any code that reads `block.thinking` (or equivalent) from a `thinking`-type block and renders it in a UI, log, or trace. **The fix is the request parameter, not the response handling** — add `display: "summarized"` to the `thinking` parameter:

```python
thinking={"type": "adaptive", "display": "summarized"}  # "display" is new on Opus 4.7; values: "omitted" (default) | "summarized"
```

The default is `"omitted"` on Claude Opus 4.7. If thinking content was never surfaced anywhere, no change needed. If your product streams reasoning to users, the new default appears as a long pause before output begins; set `display: "summarized"` to restore visible progress during thinking.

**Updated token counting.**

Claude Opus 4.7 and Claude Opus 4.6 count tokens differently. The same input text produces a higher token count on Claude Opus 4.7 than on Claude Opus 4.6, and `/v1/messages/count_tokens` will return a different number of tokens for Claude Opus 4.7 than it did for Claude Opus 4.6. The token efficiency of Claude Opus 4.7 can vary by workload shape. Prompting interventions, `task_budget`, and `effort` can help control costs and ensure appropriate token usage. Keep in mind that these controls may trade off model intelligence. **Update your `max_tokens` parameters to give additional headroom, including compaction triggers.** Claude Opus 4.7 provides a 1M context window at standard API pricing with no long-context premium.

What else to check:

- Client-side token estimators (tiktoken-style approximations) calibrated against 4.6
- Cost calculators that multiply tokens by a fixed per-token rate
- Rate-limit retry thresholds keyed to measured token counts

Re-baseline by re-running `client.messages.count_tokens()` against `claude-opus-4-7` on a representative sample of the caller's prompts. Do not apply a blanket multiplier. For cost-sensitive workloads, consider reducing `effort` by one level (e.g. `high` → `medium`). For agentic loops, consider adopting Task Budgets (below).

### New feature: Task Budgets (beta)

Opus 4.7 introduces **task budgets** — tell Claude how many tokens it has for a full agentic loop (thinking + tool calls + final output). The model sees a running countdown and uses it to prioritize work and wrap up gracefully as the budget is consumed.

This is a **suggestion the model is aware of**, not a hard cap. It is distinct from `max_tokens`, which remains the enforced per-response limit and is *not* surfaced to the model. Use `task_budget` when you want the model to self-moderate; use `max_tokens` as a hard ceiling to cap usage.

Requires beta header `task-budgets-2026-03-13`:

```python
client.beta.messages.create(
    betas=["task-budgets-2026-03-13"],
    model="claude-opus-4-7",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={
        "effort": "high",
        "task_budget": {"type": "tokens", "total": 128000},
    },
    messages=[...],
)
```

Set a generous budget for open-ended agentic tasks and tighten it for latency-sensitive ones. **Minimum `task_budget.total` is 20,000 tokens.** If the budget is too restrictive for the task, the model may complete it less thoroughly, referencing its budget as the constraint. **Do not add `task_budget` during a migration unless you are sure the budget value is right** — if you can run the workload and measure, do so; otherwise ask the user for the value rather than guessing. This is the primary lever for offsetting the token-counting shift on agentic workloads.

### Capability improvements

**High-resolution vision.** Opus 4.7 is the first Claude model with high-resolution image support. Maximum image resolution is **2576 pixels on the long edge** (up from 1568px on Opus 4.6 and prior). This unlocks gains on vision-heavy workloads, especially computer use and screenshot/artifact/document understanding. Coordinates returned by the model now map 1:1 to actual image pixels, so no scale-factor math is needed.

High-res support is **automatic on Opus 4.7** — no beta header, no client-side opt-in required. The model accepts larger inputs and returns pixel-accurate coordinates out of the box.

**Token cost.** Full-resolution images on Opus 4.7 can use up to ~3× more image tokens than on prior models (up to ~4784 tokens per image, vs. the previous ~1,600-token cap). If the extra fidelity isn't needed, downsample client-side before sending to control cost — but **do not add downsampling by default during a migration**. If you're not sure whether the pipeline needs the fidelity, ask the user rather than guessing. Use `count_tokens()` on representative images on Opus 4.7 to re-baseline before reacting to any measured cost shift.

Beyond resolution, Opus 4.7 also improves on low-level perception (pointing, measuring, counting) and natural-image bounding-box localization and detection.

**Knowledge work.** Meaningful gains on tasks where the model visually verifies its own output — `.docx` redlining, `.pptx` editing, and programmatic chart/figure analysis (e.g. pixel-level data transcription via image-processing libraries). If prompts have scaffolding like *"double-check the slide layout before returning"*, try removing it and re-baselining.

**Memory.** Opus 4.7 is better at writing and using file-system-based memory. If an agent maintains a scratchpad, notes file, or structured memory store across turns, that agent should improve at jotting down notes to itself and leveraging its notes in future tasks.

**User-facing progress updates.** Opus 4.7 provides more regular, higher-quality interim updates during long agentic traces. If the system prompt has scaffolding like *"After every 3 tool calls, summarize progress"*, try removing it to avoid excessive user-facing text. If the length or contents of Opus 4.7's updates are not well-calibrated to your use case, explicitly describe what these updates should look like in the prompt and provide examples.

### Real-time cybersecurity safeguards

Requests that involve prohibited or high-risk topics may lead to refusals.

### Fast Mode: not available on Opus 4.7

Opus 4.7 does not have a Fast Mode variant. **Opus 4.6 Fast remains supported**. Only surface this if the caller's code actually uses a Fast Mode model string (e.g. `claude-opus-4-6-fast`); if the word "fast" does not appear in the code, say nothing about Fast Mode.

When you see `model="claude-opus-4-6-fast"` (or similar), **the migration edit is**:

```python
# Opus 4.7 has no Fast Mode — keeping on 4.6 Fast (caller's choice to switch to standard Opus 4.7).
model="claude-opus-4-6-fast",
```

That is: leave the model string **unchanged**, add the comment above it, and tell the user their two options — (a) stay on Opus 4.6 Fast, which remains supported, or (b) move latency-tolerant traffic to standard Opus 4.7 for the intelligence gain. Do **not** rewrite the model string to `claude-opus-4-7` yourself; that silently trades latency for intelligence, which is the caller's decision.

### Behavioral shifts (prompt-tunable)

These don't break anything, but prompts tuned for Opus 4.6 may land differently. Opus 4.7 is more steerable than 4.6, so small prompt nudges usually close the gap.

**More literal instruction following.** Claude Opus 4.7 interprets prompts more literally and explicitly than Claude Opus 4.6, particularly at lower effort levels. It will not silently generalize an instruction from one item to another, and it will not infer requests you didn't make. The upside of this literalism is precision and less thrash. It generally performs better for API use cases with carefully tuned prompts, structured extraction, and pipelines where you want predictable behavior. A prompt and harness review may be especially helpful for migration to Claude Opus 4.7.

**Verbosity calibrates to task complexity.** Opus 4.7 scales response length to how complex it judges the task to be, rather than defaulting to a fixed verbosity — shorter answers on simple lookups, much longer on open-ended analysis. If the product depends on a particular length or style, tune the prompt explicitly. To reduce verbosity:

> *"Provide concise, focused responses. Skip non-essential context, and keep examples minimal."*

If you see specific kinds of over-verbosity (e.g. over-explaining), add instructions targeting those. Positive examples showing the desired level of concision tend to be more effective than negative examples or instructions telling the model what not to do. Do **not** assume existing "be concise" instructions should be removed — test first.

**Tone and writing style.** Opus 4.7 is more direct and opinionated, with less validation-forward phrasing and fewer emoji than Opus 4.6's warmer style. As with any new model, prose style on long-form writing may shift. If the product relies on a specific voice, re-evaluate style prompts against the new baseline. If a warmer or more conversational voice is wanted, specify it:

> *"Use a warm, collaborative tone. Acknowledge the user's framing before answering."*

**`effort` matters more than on any prior Opus.** Opus 4.7 respects `effort` levels more strictly, especially at the low end. At `low` and `medium` it scopes work to what was asked rather than going above and beyond — good for latency and cost, but on moderate tasks at `low` there is some risk of under-thinking.

- If shallow reasoning shows up on complex problems, raise `effort` to `high` or `xhigh` rather than prompting around it.
- If `effort` must stay `low` for latency, add targeted guidance: *"This task involves multi-step reasoning. Think carefully through the problem before responding."*
- **At `xhigh` or `max`, set a large `max_tokens`** so the model has room to think and act across tool calls and subagents. Start at 64K and tune from there. (`xhigh` is a new effort level on Opus 4.7, between `high` and `max`.)

Adaptive-thinking triggering is also steerable. If the model thinks more often than wanted — which can happen with large or complex system prompts — add: *"Thinking adds latency and should only be used when it will meaningfully improve answer quality — typically for problems that require multi-step reasoning. When in doubt, respond directly."*

**Uses tools less often by default.** Opus 4.7 tends to use tools less often than 4.6 and to use reasoning more. This produces better results in most cases, but for products that rely on tools (search/retrieval, function-calling, computer-use steps), it can drop tool-use rate. Two levers:

- **Raise `effort`** — `high` or `xhigh` show substantially more tool usage in agentic search and coding, and are especially useful for knowledge work.
- **Prompt for it** — be explicit in tool descriptions or the system prompt about when and how to use the tool, and encourage the model to err on the side of using it more often:

> *"When the answer depends on information not present in the conversation, you MUST call the `search` tool before answering — do not answer from prior knowledge."*

**Fewer subagents by default.** Opus 4.7 tends to spawn fewer subagents than 4.6. This is steerable — give explicit guidance on when delegation is desirable. For a coding agent, for example:

> *"Do NOT spawn a subagent for work you can complete directly in a single response (e.g. refactoring a function you can already see). Spawn multiple subagents in the same turn when fanning out across items or reading multiple files."*

**Design and frontend coding.** Opus 4.7 has stronger design instincts than 4.6, with a consistent default house style: warm cream/off-white backgrounds (around `#F4F1EA`), serif display type (Georgia, Fraunces, Playfair), italic word-accents, and a terracotta/amber accent. This reads well for editorial, hospitality, and portfolio briefs, but will feel off for dashboards, dev tools, fintech, healthcare, or enterprise apps — and it appears in slide decks as well as web UIs.

The default is persistent. Generic instructions ("don't use cream," "make it clean and minimal") tend to shift the model to a different fixed palette rather than producing variety. Two approaches work reliably:

1. **Specify a concrete alternative.** The model follows explicit specs precisely — give exact hex values, typefaces, and layout constraints.
2. **Have the model propose options before building.** This breaks the default and gives the user control:

   > *"Before building, propose 4 distinct visual directions tailored to this brief (each as: bg hex / accent hex / typeface — one-line rationale). Ask the user to pick one, then implement only that direction."*

If the caller previously relied on `temperature` for design variety, use approach (2) — it produces meaningfully different directions across runs.

Opus 4.7 also requires less frontend-design prompting than previous models to avoid generic "AI slop" aesthetics. Where earlier models needed a lengthy anti-slop snippet, Opus 4.7 generates distinctive, creative frontends with a much shorter nudge. This snippet works well alongside the variety approaches above:

> *"NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white or dark backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character. Use unique fonts, cohesive colors and themes, and animations for effects and micro-interactions."*

**Interactive coding products.** Opus 4.7's token usage and behavior can differ between autonomous, asynchronous coding agents with a single user turn and interactive, synchronous coding agents with multiple user turns. Specifically, it tends to use more tokens in interactive settings, primarily because it reasons more after user turns. This can improve long-horizon coherence, instruction following, and coding capabilities in long interactive coding sessions, but also comes with more token usage. To maximize both performance and token efficiency in coding products, use `effort: "xhigh"` or `"high"`, add autonomous features (like an auto mode), and reduce the number of human interactions required from users.

When limiting required user interactions, specify the task, intent, and relevant constraints upfront in the first human turn. Well-specified, clear, and accurate task descriptions upfront help maximize autonomy and intelligence while minimizing extra token usage after user turns — because Opus 4.7 is more autonomous than prior models, this usage pattern helps to maximize performance. In contrast, ambiguous or underspecified prompts conveyed progressively over multiple user turns tend to reduce token efficiency and sometimes performance.

**Code review.** Opus 4.7 is meaningfully better at finding bugs than prior models, with both higher recall and precision. However, if a code-review harness was tuned for an earlier model, it may initially show *lower* recall — this is likely a harness effect, not a capability regression. When a review prompt says "only report high-severity issues," "be conservative," or "don't nitpick," Opus 4.7 follows that instruction more faithfully than earlier models did: it investigates just as thoroughly, identifies the bugs, and then declines to report findings it judges to be below the stated bar. Precision rises, but measured recall can fall even though underlying bug-finding has improved.

Recommended prompt language:

> *"Report every issue you find, including ones you are uncertain about or consider low-severity. Do not filter for importance or confidence at this stage — a separate verification step will do that. Your goal here is coverage: it is better to surface a finding that later gets filtered out than to silently drop a bug. For each finding, include your confidence level and an estimated severity so a downstream filter can rank them."*

This can be used without an actual second step, but moving confidence filtering out of the finding step often helps. If the harness has a separate verification/dedup/ranking stage, tell the model explicitly that its job at the finding stage is coverage, not filtering. If single-pass self-filtering is wanted, be concrete about the bar rather than using qualitative terms like "important" — e.g. *"report any bugs that could cause incorrect behavior, a test failure, or a misleading result; only omit nits like pure style or naming preferences."* Iterate on prompts against a subset of evals to validate recall or F1 gains.

**Computer use.** Computer use works across resolutions up to the new 2576px / 3.75MP maximum. Sending images at **1080p** provides a good balance of performance and cost. For particularly cost-sensitive workloads, **720p** or **1366×768** are lower-cost options with strong performance. Test to find the ideal settings for the use case; experimenting with `effort` can also help tune behavior.

---

## Opus 4.7 Migration Checklist

Every item is tagged: **`[BLOCKS]`** items cause a 400 error, infinite loop, silent truncation, or empty output if missed — apply these as code edits, not as suggestions. **`[TUNE]`** items are quality/cost adjustments — surface them to the user as recommendations.

`[BLOCKS]` items prefixed with **"If…"** or **"At…"** are conditional. Before working through the list, **scan the file** for the conditions: does it surface thinking text to a UI/log? Does it set `output_config.effort` to `"x-high"` or `"max"`? Is it a security workload? Is it a multi-turn agentic loop? Apply only the items whose condition matches.

- [ ] **[BLOCKS]** Replace `thinking: {type: "enabled", budget_tokens: N}` with `thinking: {type: "adaptive"}` + `output_config.effort`; delete `budget_tokens` plumbing entirely
- [ ] **[BLOCKS]** Strip `temperature`, `top_p`, `top_k` from request construction
- [ ] **[BLOCKS]** If thinking content is surfaced to users or stored in logs: add `thinking.display: "summarized"` (otherwise the rendered text is empty)
- [ ] **[BLOCKS]** At `output_config.effort` of `xhigh` or `max`: set `max_tokens` ≥ 64000 (otherwise output truncates mid-thought)
- [ ] **[TUNE]** Give `max_tokens` and compaction triggers extra headroom; re-run `count_tokens()` against `claude-opus-4-7` on representative prompts to re-baseline (no blanket multiplier)
- [ ] **[TUNE]** Re-baseline cost and rate-limit dashboards *before* reacting to measured shifts
- [ ] **[TUNE]** Re-evaluate `effort` per route — use `xhigh` for coding/agentic and a minimum of `high` for most intelligence-sensitive work; it matters more on 4.7 than any prior Opus
- [ ] **[TUNE]** Multi-turn agentic loops: adopt the API-native Task Budgets (`output_config.task_budget`, beta `task-budgets-2026-03-13`, minimum 20k tokens) — this is for capping *cumulative* spend across a loop; per-turn depth is `effort`
- [ ] **[TUNE]** Check for ambiguous or underspecified instructions that relied on 4.6 generalizing intent, and update them to be clearer or more precise — 4.7 follows them literally
- [ ] **[TUNE]** Tool-use workloads: add explicit when/how-to-use guidance to tool descriptions (4.7 reaches for tools less often)
- [ ] **[TUNE]** Verbosity: test existing length instructions before changing them — 4.7 calibrates length to task complexity, so tune for the desired output rather than assuming a direction
- [ ] **[TUNE]** Remove forced-progress-update scaffolding (*"after every N tool calls…"*)
- [ ] **[TUNE]** Remove knowledge-work verification scaffolding (*"double-check the slide layout…"*) and re-baseline
- [ ] **[TUNE]** Add tone instruction if a warmer / more conversational voice is needed; re-evaluate style prompts on writing-heavy routes
- [ ] **[TUNE]** Subagent tool present: add explicit spawn / don't-spawn guidance
- [ ] **[TUNE]** Frontend/design output: specify a concrete palette/typeface, or have the model propose 4 visual directions before building (the default cream/serif house style is persistent)
- [ ] **[TUNE]** Interactive coding products: use `effort: "xhigh"` or `"high"`, add autonomous features (e.g. an auto mode) to reduce human interactions, and specify task/intent/constraints upfront in the first turn
- [ ] **[TUNE]** Code-review harnesses: remove or loosen "only report high-severity" / "be conservative" filters and have the model report every finding with confidence + severity; move filtering to a downstream step (4.7 follows severity filters more literally, which can depress measured recall)
- [ ] **[TUNE]** Vision-heavy pipelines (screenshots, charts, document understanding): leave images at native resolution up to 2576px long edge for the accuracy gain; remove any scale-factor math from coordinate handling (coords are now 1:1 with pixels). No beta header / opt-in needed — high-res is automatic on Opus 4.7.
- [ ] **[TUNE]** Computer-use pipelines: send screenshots at 1080p for a good performance/cost balance (720p or 1366×768 for cost-sensitive workloads); experiment with `effort` to tune behavior
- [ ] **[TUNE]** Cost-sensitive image pipelines: full-res images on 4.7 use up to ~4784 tokens vs ~1,600 on prior models (~3×). Downsampling client-side before upload avoids the increase, but **do not downsample by default** — if you're unsure whether fidelity is needed, ask the user. Re-baseline with `count_tokens()` on representative images before reacting to cost shifts.

---

## Verify the Migration

After updating, spot-check that the new model is actually being used. Replace `YOUR_TARGET_MODEL` with the model string you migrated to (e.g. `claude-opus-4-7`, `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5`) and keep the assertion prefix in sync:

```python
YOUR_TARGET_MODEL = "claude-opus-4-7"  # or "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"
response = client.messages.create(model=YOUR_TARGET_MODEL, max_tokens=64, messages=[...])
assert response.model.startswith(YOUR_TARGET_MODEL), response.model
```

For rate-limit headroom changes, pricing, or capability deltas (vision, structured outputs, effort support), query the Models API:

```python
m = client.models.retrieve(YOUR_TARGET_MODEL)
m.max_input_tokens, m.max_tokens
m.capabilities["effort"]["max"]["supported"]
```

See `shared/models.md` for the full capability lookup pattern.
# Claude Model Catalog

**Only use exact model IDs listed in this file.** Never guess or construct model IDs — incorrect IDs will cause API errors. Use aliases wherever available. For the latest information, WebFetch the Models Overview URL in `shared/live-sources.md`, or query the Models API directly (see Programmatic Model Discovery below).

## Programmatic Model Discovery

For **live** capability data — context window, max output tokens, feature support (thinking, vision, effort, structured outputs, etc.) — query the Models API instead of relying on the cached tables below. Use this when the user asks "what's the context window for X", "does model X support vision/thinking/effort", "which models support feature Y", or wants to select a model by capability at runtime.

```python
m = client.models.retrieve("claude-opus-4-7")
m.id                 # "claude-opus-4-7"
m.display_name       # "Claude Opus 4.7"
m.max_input_tokens   # context window (int)
m.max_tokens         # max output tokens (int)

# capabilities is an untyped nested dict — bracket access, check ["supported"] at the leaf
caps = m.capabilities
caps["image_input"]["supported"]                       # vision
caps["thinking"]["types"]["adaptive"]["supported"]     # adaptive thinking
caps["effort"]["max"]["supported"]                     # effort: max (also low/medium/high)
caps["structured_outputs"]["supported"]
caps["context_management"]["compact_20260112"]["supported"]

# filter across all models — iterate the page object directly (auto-paginates); do NOT use .data
[m for m in client.models.list()
 if m.capabilities["thinking"]["types"]["adaptive"]["supported"]
 and m.max_input_tokens >= 200_000]
```

Top-level fields (`id`, `display_name`, `max_input_tokens`, `max_tokens`) are typed attributes. `capabilities` is a dict — use bracket access, not attribute access. The API returns the full capability tree for every model with `supported: true/false` at each leaf, so bracket chains are safe without `.get()` guards. TypeScript SDK: same method names, also auto-paginates on iteration.

### Raw HTTP

```bash
curl https://api.anthropic.com/v1/models/claude-opus-4-7 \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01"
```

```json
{
  "id": "claude-opus-4-7",
  "display_name": "Claude Opus 4.7",
  "max_input_tokens": 200000,
  "max_tokens": 128000,
  "capabilities": {
    "image_input": {"supported": true},
    "structured_outputs": {"supported": true},
    "thinking": {"supported": true, "types": {"enabled": {"supported": false}, "adaptive": {"supported": true}}},
    "effort": {"supported": true, "low": {"supported": true}, …, "max": {"supported": true}},
    …
  }
}
```

## Current Models (recommended)

| Friendly Name     | Alias (use this)    | Full ID                       | Context        | Max Output | Status |
|-------------------|---------------------|-------------------------------|----------------|------------|--------|
| Claude Opus 4.7   | `claude-opus-4-7`   | —                             | 1M             | 128K       | Active |
| Claude Opus 4.6   | `claude-opus-4-6`   | —                             | 1M             | 128K       | Active |
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | -                             | 1M             | 64K        | Active |
| Claude Haiku 4.5  | `claude-haiku-4-5`  | `claude-haiku-4-5-20251001`   | 200K           | 64K        | Active |

### Model Descriptions
- **Claude Opus 4.7** — The most capable Claude model to date — highly autonomous, strong on long-horizon agentic work, knowledge work, vision, and memory. Adaptive thinking only; sampling parameters and `budget_tokens` are removed. 1M context window at standard API pricing (no long-context premium) — see `shared/model-migration.md` → Migrating to Opus 4.7 for breaking changes.
- **Claude Opus 4.6** — Previous-generation Opus. Supports adaptive thinking (recommended), 128K max output tokens (requires streaming for large outputs). 1M context window.
- **Claude Sonnet 4.6** — Our best combination of speed and intelligence. Supports adaptive thinking (recommended). 1M context window. 64K max output tokens.
- **Claude Haiku 4.5** — Fastest and most cost-effective model for simple tasks.

## Legacy Models (still active)

| Friendly Name     | Alias (use this)    | Full ID                       | Status |
|-------------------|---------------------|-------------------------------|--------|
| Claude Opus 4.5   | `claude-opus-4-5`   | `claude-opus-4-5-20251101`    | Active |
| Claude Opus 4.1   | `claude-opus-4-1`   | `claude-opus-4-1-20250805`    | Active |
| Claude Sonnet 4.5 | `claude-sonnet-4-5` | `claude-sonnet-4-5-20250929`  | Active |
| Claude Sonnet 4   | `claude-sonnet-4-0` | `claude-sonnet-4-20250514`    | Active |
| Claude Opus 4     | `claude-opus-4-0`   | `claude-opus-4-20250514`      | Active |

## Deprecated Models (retiring soon)

| Friendly Name     | Alias (use this)    | Full ID                       | Status     | Retires      |
|-------------------|---------------------|-------------------------------|------------|--------------|
| Claude Haiku 3    | —                   | `claude-3-haiku-20240307`     | Deprecated | Apr 19, 2026 |

## Retired Models (no longer available)

| Friendly Name     | Full ID                       | Retired     |
|-------------------|-------------------------------|-------------|
| Claude Sonnet 3.7 | `claude-3-7-sonnet-20250219`  | Feb 19, 2026 |
| Claude Haiku 3.5  | `claude-3-5-haiku-20241022`   | Feb 19, 2026 |
| Claude Opus 3     | `claude-3-opus-20240229`      | Jan 5, 2026 |
| Claude Sonnet 3.5 | `claude-3-5-sonnet-20241022`  | Oct 28, 2025 |
| Claude Sonnet 3.5 | `claude-3-5-sonnet-20240620`  | Oct 28, 2025 |
| Claude Sonnet 3   | `claude-3-sonnet-20240229`    | Jul 21, 2025 |
| Claude 2.1        | `claude-2.1`                  | Jul 21, 2025 |
| Claude 2.0        | `claude-2.0`                  | Jul 21, 2025 |

## Resolving User Requests

When a user asks for a model by name, use this table to find the correct model ID:

| User says...                              | Use this model ID              |
|-------------------------------------------|--------------------------------|
| "opus", "most powerful"                   | `claude-opus-4-7`              |
| "opus 4.7"                                | `claude-opus-4-7`              |
| "opus 4.6"                                | `claude-opus-4-6`              |
| "opus 4.5"                                | `claude-opus-4-5`              |
| "opus 4.1"                                | `claude-opus-4-1`              |
| "opus 4", "opus 4.0"                      | `claude-opus-4-0`              |
| "sonnet", "balanced"                      | `claude-sonnet-4-6`            |
| "sonnet 4.6"                              | `claude-sonnet-4-6`            |
| "sonnet 4.5"                              | `claude-sonnet-4-5`            |
| "sonnet 4", "sonnet 4.0"                  | `claude-sonnet-4-0`            |
| "sonnet 3.7"                              | Retired — suggest `claude-sonnet-4-5` |
| "sonnet 3.5"                              | Retired — suggest `claude-sonnet-4-5` |
| "haiku", "fast", "cheap"                  | `claude-haiku-4-5`             |
| "haiku 4.5"                               | `claude-haiku-4-5`             |
| "haiku 3.5"                               | Retired — suggest `claude-haiku-4-5` |
| "haiku 3"                                 | Deprecated — suggest `claude-haiku-4-5` |
# Prompt Caching — Design & Optimization

This file covers how to design prompt-building code for effective caching. For language-specific syntax, see the `## Prompt Caching` section in each language's README or single-file doc.

## The one invariant everything follows from

**Prompt caching is a prefix match. Any change anywhere in the prefix invalidates everything after it.**

The cache key is derived from the exact bytes of the rendered prompt up to each `cache_control` breakpoint. A single byte difference at position N — a timestamp, a reordered JSON key, a different tool in the list — invalidates the cache for all breakpoints at positions ≥ N.

Render order is: `tools` → `system` → `messages`. A breakpoint on the last system block caches both tools and system together.

Design the prompt-building path around this constraint. Get the ordering right and most caching works for free. Get it wrong and no amount of `cache_control` markers will help.

---

## Workflow for optimizing existing code

When asked to add or optimize caching:

1. **Trace the prompt assembly path.** Find where `system`, `tools`, and `messages` are constructed. Identify every input that flows into them.
2. **Classify each input by stability:**
   - Never changes → belongs early in the prompt, before any breakpoint
   - Changes per-session → belongs after the global prefix, cache per-session
   - Changes per-turn → belongs at the end, after the last breakpoint
   - Changes per-request (timestamps, UUIDs, random IDs) → **eliminate or move to the very end**
3. **Check rendered order matches stability order.** Stable content must physically precede volatile content. If a timestamp is interpolated into the system prompt header, everything after it is uncacheable regardless of markers.
4. **Place breakpoints at stability boundaries.** See placement patterns below.
5. **Audit for silent invalidators.** See anti-patterns table.

---

## Placement patterns

### Large system prompt shared across many requests

Put a breakpoint on the last system text block. If there are tools, they render before system — the marker on the last system block caches tools + system together.

```json
"system": [
  {"type": "text", "text": "<large shared prompt>", "cache_control": {"type": "ephemeral"}}
]
```

### Multi-turn conversations

Put a breakpoint on the last content block of the most-recently-appended turn. Each subsequent request reuses the entire prior conversation prefix. Earlier breakpoints remain valid read points, so hits accrue incrementally as the conversation grows.

```json
// Last content block of the last user turn
messages[-1].content[-1].cache_control = {"type": "ephemeral"}
```

### Shared prefix, varying suffix

Many requests share a large fixed preamble (few-shot examples, retrieved docs, instructions) but differ in the final question. Put the breakpoint at the end of the **shared** portion, not at the end of the whole prompt — otherwise every request writes a distinct cache entry and nothing is ever read.

```json
"messages": [{"role": "user", "content": [
  {"type": "text", "text": "<shared context>", "cache_control": {"type": "ephemeral"}},
  {"type": "text", "text": "<varying question>"}  // no marker — differs every time
]}]
```

### Prompts that change from the beginning every time

Don't cache. If the first 1K tokens differ per request, there is no reusable prefix. Adding `cache_control` only pays the cache-write premium with zero reads. Leave it off.

---

## Architectural guidance

These are the decisions that matter more than marker placement. Fix these first.

**Keep the system prompt frozen.** Don't interpolate "current date: X", "mode: Y", "user name: Z" into the system prompt — those sit at the front of the prefix and invalidate everything downstream. Inject dynamic context as a user or assistant message later in `messages`. A message at turn 5 invalidates nothing before turn 5.

**Don't change tools or model mid-conversation.** Tools render at position 0; adding, removing, or reordering a tool invalidates the entire cache. Same for switching models (caches are model-scoped). If you need "modes", don't swap the tool set — give Claude a tool that records the mode transition, or pass the mode as message content. Serialize tools deterministically (sort by name).

**Fork operations must reuse the parent's exact prefix.** Side computations (summarization, compaction, sub-agents) often spin up a separate API call. If the fork rebuilds `system` / `tools` / `model` with any difference, it misses the parent's cache entirely. Copy the parent's `system`, `tools`, and `model` verbatim, then append fork-specific content at the end.

---

## Silent invalidators

When reviewing code, grep for these inside anything that feeds the prompt prefix:

| Pattern | Why it breaks caching |
|---|---|
| `datetime.now()` / `Date.now()` / `time.time()` in system prompt | Prefix changes every request |
| `uuid4()` / `crypto.randomUUID()` / request IDs early in content | Same — every request is unique |
| `json.dumps(d)` without `sort_keys=True` / iterating a `set` | Non-deterministic serialization → prefix bytes differ |
| f-string interpolating session/user ID into system prompt | Per-user prefix; no cross-user sharing |
| Conditional system sections (`if flag: system += ...`) | Every flag combination is a distinct prefix |
| `tools=build_tools(user)` where set varies per user | Tools render at position 0; nothing caches across users |

Fix by moving the dynamic piece after the last breakpoint, making it deterministic, or deleting it if it's not load-bearing.

---

## API reference

```json
"cache_control": {"type": "ephemeral"}              // 5-minute TTL (default)
"cache_control": {"type": "ephemeral", "ttl": "1h"} // 1-hour TTL
```

- Max **4** `cache_control` breakpoints per request.
- Goes on any content block: system text blocks, tool definitions, message content blocks (`text`, `image`, `tool_use`, `tool_result`, `document`).
- Top-level `cache_control` on `messages.create()` auto-places on the last cacheable block — simplest option when you don't need fine-grained placement.
- Minimum cacheable prefix is model-dependent. Shorter prefixes silently won't cache even with a marker — no error, just `cache_creation_input_tokens: 0`:

| Model | Minimum |
|---|---:|
| Opus 4.7, Opus 4.6, Opus 4.5, Haiku 4.5 | 4096 tokens |
| Sonnet 4.6, Haiku 3.5, Haiku 3 | 2048 tokens |
| Sonnet 4.5, Sonnet 4.1, Sonnet 4, Sonnet 3.7 | 1024 tokens |

A 3K-token prompt caches on Sonnet 4.5 but silently won't on Opus 4.7.

**Economics:** Cache reads cost ~0.1× base input price. Cache writes cost **1.25× for 5-minute TTL, 2× for 1-hour TTL**. Break-even depends on TTL: with 5-minute TTL, two requests break even (1.25× + 0.1× = 1.35× vs 2× uncached); with 1-hour TTL, you need at least three requests (2× + 0.2× = 2.2× vs 3× uncached). The 1-hour TTL keeps entries alive across gaps in bursty traffic, but the doubled write cost means it needs more reads to pay off.

---

## Verifying cache hits

The response `usage` object reports cache activity:

| Field | Meaning |
|---|---|
| `cache_creation_input_tokens` | Tokens written to cache this request (you paid the ~1.25× write premium) |
| `cache_read_input_tokens` | Tokens served from cache this request (you paid ~0.1×) |
| `input_tokens` | Tokens processed at full price (not cached) |

If `cache_read_input_tokens` is zero across repeated requests with identical prefixes, a silent invalidator is at work — diff the rendered prompt bytes between two requests to find it.

**`input_tokens` is the uncached remainder only.** Total prompt size = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. If your agent ran for hours but `input_tokens` shows 4K, the rest was served from cache — check the sum, not the single field.

Language-specific access: `response.usage.cache_read_input_tokens` (Python/TS/Ruby), `$message->usage->cacheReadInputTokens` (PHP), `resp.Usage.CacheReadInputTokens` (Go/C#), `.usage().cacheReadInputTokens()` (Java).

---

## Invalidation hierarchy

Not every parameter change invalidates everything. The API has three cache tiers, and changes only invalidate their own tier and below:

| Change | Tools cache | System cache | Messages cache |
|---|:---:|:---:|:---:|
| Tool definitions (add/remove/reorder) | ❌ | ❌ | ❌ |
| Model switch | ❌ | ❌ | ❌ |
| `speed`, web-search, citations toggle | ✅ | ❌ | ❌ |
| System prompt content | ✅ | ❌ | ❌ |
| `tool_choice`, images, `thinking` enable/disable | ✅ | ✅ | ❌ |
| Message content | ✅ | ✅ | ❌ |

Implication: you can change `tool_choice` per-request or toggle `thinking` without losing the tools+system cache. Don't over-worry about these — only tool-definition and model changes force a full rebuild.

---

## 20-block lookback window

Each breakpoint walks backward **at most 20 content blocks** to find a prior cache entry. If a single turn adds more than 20 blocks (common in agentic loops with many tool_use/tool_result pairs), the next request's breakpoint won't find the previous cache and silently misses.

Fix: place an intermediate breakpoint every ~15 blocks in long turns, or put the marker on a block that's within 20 of the previous turn's last cached block.

---

## Concurrent-request timing

A cache entry becomes readable only after the first response **begins streaming**. N parallel requests with identical prefixes all pay full price — none can read what the others are still writing.

For fan-out patterns: send 1 request, await the first streamed token (not the full response), then fire the remaining N−1. They'll read the cache the first one just wrote.
# Tool Use Concepts

This file covers the conceptual foundations of tool use with the Claude API. For language-specific code examples, see the `python/`, `typescript/`, or other language folders. For decision heuristics on which tools to expose, how to manage context in long-running agents, and caching strategy, see `agent-design.md`.

## User-Defined Tools

### Tool Definition Structure

> **Note:** When using the Tool Runner (beta), tool schemas are generated automatically from your function signatures (Python), Zod schemas (TypeScript), annotated classes (Java), `jsonschema` struct tags (Go), or `BaseTool` subclasses (Ruby). The raw JSON schema format below is for the manual approach — including PHP's `BetaRunnableTool`, which wraps a run closure around a hand-written schema — or SDKs without tool runner support.

Each tool requires a name, description, and JSON Schema for its inputs:

```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "input_schema": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City and state, e.g., San Francisco, CA"
      },
      "unit": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "description": "Temperature unit"
      }
    },
    "required": ["location"]
  }
}
```

**Best practices for tool definitions:**

- Use clear, descriptive names (e.g., `get_weather`, `search_database`, `send_email`)
- Write detailed descriptions — Claude uses these to decide when to use the tool
- Include descriptions for each property
- Use `enum` for parameters with a fixed set of values
- Mark truly required parameters in `required`; make others optional with defaults

---

### Tool Choice Options

Control when Claude uses tools:

| Value                             | Behavior                                      |
| --------------------------------- | --------------------------------------------- |
| `{"type": "auto"}`                | Claude decides whether to use tools (default) |
| `{"type": "any"}`                 | Claude must use at least one tool             |
| `{"type": "tool", "name": "..."}` | Claude must use the specified tool            |
| `{"type": "none"}`                | Claude cannot use tools                       |

Any `tool_choice` value can also include `"disable_parallel_tool_use": true` to force Claude to use at most one tool per response. By default, Claude may request multiple tool calls in a single response.

---

### Tool Runner vs Manual Loop

**Tool Runner (Recommended):** The SDK's tool runner handles the agentic loop automatically — it calls the API, detects tool use requests, executes your tool functions, feeds results back to Claude, and repeats until Claude stops calling tools. Available in Python, TypeScript, Java, Go, Ruby, and PHP SDKs (beta). The Python SDK also provides MCP conversion helpers (`anthropic.lib.tools.mcp`) to convert MCP tools, prompts, and resources for use with the tool runner — see `python/claude-api/tool-use.md` for details.

**Manual Agentic Loop:** Use when you need fine-grained control over the loop (e.g., custom logging, conditional tool execution, human-in-the-loop approval). Loop until `stop_reason == "end_turn"`, always append the full `response.content` to preserve tool_use blocks, and ensure each `tool_result` includes the matching `tool_use_id`.

**Stop reasons for server-side tools:** When using server-side tools (code execution, web search, etc.), the API runs a server-side sampling loop. If this loop reaches its default limit of 10 iterations, the response will have `stop_reason: "pause_turn"`. To continue, re-send the user message and assistant response and make another API request — the server will resume where it left off. Do NOT add an extra user message like "Continue." — the API detects the trailing `server_tool_use` block and knows to resume automatically.

```python
# Handle pause_turn in your agentic loop
if response.stop_reason == "pause_turn":
    messages = [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": response.content},
    ]
    # Make another API request — server resumes automatically
    response = client.messages.create(
        model="claude-opus-4-7", messages=messages, tools=tools
    )
```

Set a `max_continuations` limit (e.g., 5) to prevent infinite loops. For the full guide, see: `https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons`

> **Security:** The tool runner executes your tool functions automatically whenever Claude requests them. For tools with side effects (sending emails, modifying databases, financial transactions), validate inputs within your tool functions and consider requiring confirmation for destructive operations. Use the manual agentic loop if you need human-in-the-loop approval before each tool execution.

---

### Handling Tool Results

When Claude uses a tool, the response contains a `tool_use` block. You must:

1. Execute the tool with the provided input
2. Send the result back in a `tool_result` message
3. Continue the conversation

**Error handling in tool results:** When a tool execution fails, set `"is_error": true` and provide an informative error message. Claude will typically acknowledge the error and either try a different approach or ask for clarification.

**Multiple tool calls:** Claude can request multiple tools in a single response. Handle them all before continuing — send all results back in a single `user` message.

---

## Server-Side Tools: Code Execution

The code execution tool lets Claude run code in a secure, sandboxed container. Unlike user-defined tools, server-side tools run on Anthropic's infrastructure — you don't execute anything client-side. Just include the tool definition and Claude handles the rest.

### Key Facts

- Runs in an isolated container (1 CPU, 5 GiB RAM, 5 GiB disk)
- No internet access (fully sandboxed)
- Python 3.11 with data science libraries pre-installed
- Containers persist for 30 days and can be reused across requests
- Free when used with web search/web fetch tools; otherwise $0.05/hour after 1,550 free hours/month per organization

### Tool Definition

The tool requires no schema — just declare it in the `tools` array:

```json
{
  "type": "code_execution_20260120",
  "name": "code_execution"
}
```

Claude automatically gains access to `bash_code_execution` (run shell commands) and `text_editor_code_execution` (create/view/edit files).

### Pre-installed Python Libraries

- **Data science**: pandas, numpy, scipy, scikit-learn, statsmodels
- **Visualization**: matplotlib, seaborn
- **File processing**: openpyxl, xlsxwriter, pillow, pypdf, pdfplumber, python-docx, python-pptx
- **Math**: sympy, mpmath
- **Utilities**: tqdm, python-dateutil, pytz, sqlite3

Additional packages can be installed at runtime via `pip install`.

### Supported File Types for Upload

| Type   | Extensions                         |
| ------ | ---------------------------------- |
| Data   | CSV, Excel (.xlsx/.xls), JSON, XML |
| Images | JPEG, PNG, GIF, WebP               |
| Text   | .txt, .md, .py, .js, etc.          |

### Container Reuse

Reuse containers across requests to maintain state (files, installed packages, variables). Extract the `container_id` from the first response and pass it to subsequent requests.

### Response Structure

The response contains interleaved text and tool result blocks:

- `text` — Claude's explanation
- `server_tool_use` — What Claude is doing
- `bash_code_execution_tool_result` — Code execution output (check `return_code` for success/failure)
- `text_editor_code_execution_tool_result` — File operation results

> **Security:** Always sanitize filenames with `os.path.basename()` / `path.basename()` before writing downloaded files to disk to prevent path traversal attacks. Write files to a dedicated output directory.

---

## Server-Side Tools: Web Search and Web Fetch

Web search and web fetch let Claude search the web and retrieve page content. They run server-side — just include the tool definitions and Claude handles queries, fetching, and result processing automatically.

### Tool Definitions

```json
[
  { "type": "web_search_20260209", "name": "web_search" },
  { "type": "web_fetch_20260209", "name": "web_fetch" }
]
```

### Dynamic Filtering (Opus 4.7 / Opus 4.6 / Sonnet 4.6)

The `web_search_20260209` and `web_fetch_20260209` versions support **dynamic filtering** — Claude writes and executes code to filter search results before they reach the context window, improving accuracy and token efficiency. Dynamic filtering is built into these tool versions and activates automatically; you do not need to separately declare the `code_execution` tool or pass any beta header.

```json
{
  "tools": [
    { "type": "web_search_20260209", "name": "web_search" },
    { "type": "web_fetch_20260209", "name": "web_fetch" }
  ]
}
```

Without dynamic filtering, the previous `web_search_20250305` version is also available.

> **Note:** Only include the standalone `code_execution` tool when your application needs code execution for its own purposes (data analysis, file processing, visualization) independent of web search. Including it alongside `_20260209` web tools creates a second execution environment that can confuse the model.

---

## Server-Side Tools: Programmatic Tool Calling

With standard tool use, each tool call is a round trip: Claude calls, the result enters Claude's context, Claude reasons, then calls the next tool. Chained calls accumulate latency and tokens — most of that intermediate data is never needed again.

Programmatic tool calling lets Claude compose those calls into a script. The script runs in the code execution container; when it invokes a tool, the container pauses, the call executes, and the result returns to the running code (not to Claude's context). The script processes it with normal control flow. Only the final output returns to Claude. Use it when chaining many tool calls or when intermediate results are large and should be filtered before reaching the context window.

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling`

---

## Server-Side Tools: Tool Search

The tool search tool lets Claude dynamically discover tools from large libraries without loading all definitions into the context window. Use it when you have many tools but only a few are relevant to any given request. Discovered tool schemas are appended to the request, not swapped in — this preserves the prompt cache (see `agent-design.md` §Caching for Agents).

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool`

---

## Skills

Skills package task-specific instructions that Claude loads only when relevant. Each skill is a folder containing a `SKILL.md` file. The skill's short description sits in context by default; Claude reads the full file when the current task calls for it. Use skills to keep specialized instructions out of the base system prompt without losing discoverability.

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/skills`

---

## Tool Use Examples

You can provide sample tool calls directly in your tool definitions to demonstrate usage patterns and reduce parameter errors. This helps Claude understand how to correctly format tool inputs, especially for tools with complex schemas.

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use`

---

## Server-Side Tools: Computer Use

Computer use lets Claude interact with a desktop environment (screenshots, mouse, keyboard). It can be Anthropic-hosted (server-side, like code execution) or self-hosted (you provide the environment and execute actions client-side).

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/computer-use/overview`

---

## Context Editing

Context editing clears stale tool results and thinking blocks from the transcript as a long-running agent accumulates turns. Unlike compaction (which summarizes), context editing prunes — the cleared content is removed, not replaced. Use it when old tool outputs are no longer relevant and you want to keep the transcript lean without losing the conversation structure. Thresholds for what to clear are configurable.

For full documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/build-with-claude/context-editing`

---

## Client-Side Tools: Memory

The memory tool enables Claude to store and retrieve information across conversations through a memory file directory. Claude can create, read, update, and delete files that persist between sessions.

### Key Facts

- Client-side tool — you control storage via your implementation
- Supports commands: `view`, `create`, `str_replace`, `insert`, `delete`, `rename`
- Operates on files in a `/memories` directory
- The Python, TypeScript, and Java SDKs provide helper classes/functions for implementing the memory backend

> **Security:** Never store API keys, passwords, tokens, or other secrets in memory files. Be cautious with personally identifiable information (PII) — check data privacy regulations (GDPR, CCPA) before persisting user data. The reference implementations have no built-in access control; in multi-user systems, implement per-user memory directories and authentication in your tool handlers.

For full implementation examples, use WebFetch:

- Docs: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool.md`

---

## Structured Outputs

Structured outputs constrain Claude's responses to follow a specific JSON schema, guaranteeing valid, parseable output. This is not a separate tool — it enhances the Messages API response format and/or tool parameter validation.

Two features are available:

- **JSON outputs** (`output_config.format`): Control Claude's response format
- **Strict tool use** (`strict: true`): Guarantee valid tool parameter schemas

**Supported models:** Claude Opus 4.7, Claude Sonnet 4.6, and Claude Haiku 4.5. Legacy models (Claude Opus 4.5, Claude Opus 4.1) also support structured outputs.

> **Recommended:** Use `client.messages.parse()` which automatically validates responses against your schema. When using `messages.create()` directly, use `output_config: {format: {...}}`. The `output_format` convenience parameter is also accepted by some SDK methods (e.g., `.parse()`), but `output_config.format` is the canonical API-level parameter.

### JSON Schema Limitations

**Supported:**

- Basic types: object, array, string, integer, number, boolean, null
- `enum`, `const`, `anyOf`, `allOf`, `$ref`/`$def`
- String formats: `date-time`, `time`, `date`, `duration`, `email`, `hostname`, `uri`, `ipv4`, `ipv6`, `uuid`
- `additionalProperties: false` (required for all objects)

**Not supported:**

- Recursive schemas
- Numerical constraints (`minimum`, `maximum`, `multipleOf`)
- String constraints (`minLength`, `maxLength`)
- Complex array constraints
- `additionalProperties` set to anything other than `false`

The Python and TypeScript SDKs automatically handle unsupported constraints by removing them from the schema sent to the API and validating them client-side.

### Important Notes

- **First request latency**: New schemas incur a one-time compilation cost. Subsequent requests with the same schema use a 24-hour cache.
- **Refusals**: If Claude refuses for safety reasons (`stop_reason: "refusal"`), the output may not match your schema.
- **Token limits**: If `stop_reason: "max_tokens"`, output may be incomplete. Increase `max_tokens`.
- **Incompatible with**: Citations (returns 400 error), message prefilling.
- **Works with**: Batches API, streaming, token counting, extended thinking.

---

## Tips for Effective Tool Use

1. **Provide detailed descriptions**: Claude relies heavily on descriptions to understand when and how to use tools
2. **Use specific tool names**: `get_current_weather` is better than `weather`
3. **Validate inputs**: Always validate tool inputs before execution
4. **Handle errors gracefully**: Return informative error messages so Claude can adapt
5. **Limit tool count**: Too many tools can confuse the model — keep the set focused
6. **Test tool interactions**: Verify Claude uses tools correctly in various scenarios

For detailed tool use documentation, use WebFetch:

- URL: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview`
# HTTP Error Codes Reference

This file documents HTTP error codes returned by the Claude API, their common causes, and how to handle them. For language-specific error handling examples, see the `python/` or `typescript/` folders.

## Error Code Summary

| Code | Error Type              | Retryable | Common Cause                         |
| ---- | ----------------------- | --------- | ------------------------------------ |
| 400  | `invalid_request_error` | No        | Invalid request format or parameters |
| 401  | `authentication_error`  | No        | Invalid or missing API key           |
| 403  | `permission_error`      | No        | API key lacks permission             |
| 404  | `not_found_error`       | No        | Invalid endpoint or model ID         |
| 413  | `request_too_large`     | No        | Request exceeds size limits          |
| 429  | `rate_limit_error`      | Yes       | Too many requests                    |
| 500  | `api_error`             | Yes       | Anthropic service issue              |
| 529  | `overloaded_error`      | Yes       | API is temporarily overloaded        |

## Detailed Error Information

### 400 Bad Request

**Causes:**

- Malformed JSON in request body
- Missing required parameters (`model`, `max_tokens`, `messages`)
- Invalid parameter types (e.g., string where integer expected)
- Empty messages array
- Messages not alternating user/assistant

**Example error:**

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "messages: roles must alternate between \"user\" and \"assistant\""
  },
  "request_id": "req_011CSHoEeqs5C35K2UUqR7Fy"
}
```

**Fix:** Validate request structure before sending. Check that:

- `model` is a valid model ID
- `max_tokens` is a positive integer
- `messages` array is non-empty and alternates correctly

---

### 401 Unauthorized

**Causes:**

- Missing `x-api-key` header or `Authorization` header
- Invalid API key format
- Revoked or deleted API key

**Fix:** Ensure `ANTHROPIC_API_KEY` environment variable is set correctly.

---

### 403 Forbidden

**Causes:**

- API key doesn't have access to the requested model
- Organization-level restrictions
- Attempting to access beta features without beta access

**Fix:** Check your API key permissions in the Console. You may need a different API key or to request access to specific features.

---

### 404 Not Found

**Causes:**

- Typo in model ID (e.g., `claude-sonnet-4.6` instead of `claude-sonnet-4-6`)
- Using deprecated model ID
- Invalid API endpoint

**Fix:** Use exact model IDs from the models documentation. You can use aliases (e.g., `claude-opus-4-7`).

---

### 413 Request Too Large

**Causes:**

- Request body exceeds maximum size
- Too many tokens in input
- Image data too large

**Fix:** Reduce input size — truncate conversation history, compress/resize images, or split large documents into chunks.

---

### 400 Validation Errors

Some 400 errors are specifically related to parameter validation:

- `max_tokens` exceeds model's limit
- Invalid `temperature` value (must be 0.0-1.0)
- `budget_tokens` >= `max_tokens` in extended thinking
- Invalid tool definition schema

**Model-specific 400s on Opus 4.7:**

- `temperature`, `top_p`, `top_k` are removed — sending any of them returns 400. Delete the parameter; see `shared/model-migration.md` → Per-SDK Syntax Reference.
- `thinking: {type: "enabled", budget_tokens: N}` is removed — sending it returns 400. Use `thinking: {type: "adaptive"}` instead.

**Common mistake with extended thinking on older models (Opus 4.6 and earlier):**

```
# Wrong: budget_tokens must be < max_tokens
thinking: budget_tokens=10000, max_tokens=1000  → Error!

# Correct
thinking: budget_tokens=10000, max_tokens=16000
```

---

### 429 Rate Limited

**Causes:**

- Exceeded requests per minute (RPM)
- Exceeded tokens per minute (TPM)
- Exceeded tokens per day (TPD)

**Headers to check:**

- `retry-after`: Seconds to wait before retrying
- `x-ratelimit-limit-*`: Your limits
- `x-ratelimit-remaining-*`: Remaining quota

**Fix:** The Anthropic SDKs automatically retry 429 and 5xx errors with exponential backoff (default: `max_retries=2`). For custom retry behavior, see the language-specific error handling examples.

---

### 500 Internal Server Error

**Causes:**

- Temporary Anthropic service issue
- Bug in API processing

**Fix:** Retry with exponential backoff. If persistent, check [status.anthropic.com](https://status.anthropic.com).

---

### 529 Overloaded

**Causes:**

- High API demand
- Service capacity reached

**Fix:** Retry with exponential backoff. Consider using a different model (Haiku is often less loaded), spreading requests over time, or implementing request queuing.

---

## Common Mistakes and Fixes

| Mistake                         | Error            | Fix                                                     |
| ------------------------------- | ---------------- | ------------------------------------------------------- |
| `temperature`/`top_p`/`top_k` on Opus 4.7 | 400    | Remove the parameter (see `shared/model-migration.md`)  |
| `budget_tokens` on Opus 4.7     | 400              | Use `thinking: {type: "adaptive"}`                      |
| `budget_tokens` >= `max_tokens` (older models) | 400 | Ensure `budget_tokens` < `max_tokens`                  |
| Typo in model ID                | 404              | Use valid model ID like `claude-opus-4-7`               |
| First message is `assistant`    | 400              | First message must be `user`                            |
| Consecutive same-role messages  | 400              | Alternate `user` and `assistant`                        |
| API key in code                 | 401 (leaked key) | Use environment variable                                |
| Custom retry needs              | 429/5xx          | SDK retries automatically; customize with `max_retries` |

## Typed Exceptions in SDKs

**Always use the SDK's typed exception classes** instead of checking error messages with string matching. Each HTTP error code maps to a specific exception class:

| HTTP Code | TypeScript Class                  | Python Class                      |
| --------- | --------------------------------- | --------------------------------- |
| 400       | `Anthropic.BadRequestError`       | `anthropic.BadRequestError`       |
| 401       | `Anthropic.AuthenticationError`   | `anthropic.AuthenticationError`   |
| 403       | `Anthropic.PermissionDeniedError` | `anthropic.PermissionDeniedError` |
| 404       | `Anthropic.NotFoundError`         | `anthropic.NotFoundError`         |
| 429       | `Anthropic.RateLimitError`        | `anthropic.RateLimitError`        |
| 500+      | `Anthropic.InternalServerError`   | `anthropic.InternalServerError`   |
| Any       | `Anthropic.APIError`              | `anthropic.APIError`              |

```typescript
// ✅ Correct: use typed exceptions
try {
  const response = await client.messages.create({...});
} catch (error) {
  if (error instanceof Anthropic.RateLimitError) {
    // Handle rate limiting
  } else if (error instanceof Anthropic.APIError) {
    console.error(`API error ${error.status}:`, error.message);
  }
}

// ❌ Wrong: don't check error messages with string matching
try {
  const response = await client.messages.create({...});
} catch (error) {
  const msg = error instanceof Error ? error.message : String(error);
  if (msg.includes("429") || msg.includes("rate_limit")) { ... }
}
```

All exception classes extend `Anthropic.APIError`, which has a `status` property. Use `instanceof` checks from most specific to least specific (e.g., check `RateLimitError` before `APIError`).
# Live Documentation Sources

This file contains WebFetch URLs for fetching current information from platform.claude.com and Agent SDK repositories. Use these when users need the latest data that may have changed since the cached content was last updated.

## When to Use WebFetch

- User explicitly asks for "latest" or "current" information
- Cached data seems incorrect
- User asks about features not covered in cached content
- User needs specific API details or examples

## Claude API Documentation URLs

### Models & Pricing

| Topic           | URL                                                                          | Extraction Prompt                                                               |
| --------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Models Overview | `https://platform.claude.com/docs/en/about-claude/models/overview.md`        | "Extract current model IDs, context windows, and pricing for all Claude models" |
| Migration Guide | `https://platform.claude.com/docs/en/about-claude/models/migration-guide.md` | "Extract breaking changes, deprecated parameters, and per-model migration steps when moving to a newer Claude model" |
| Pricing         | `https://platform.claude.com/docs/en/pricing.md`                             | "Extract current pricing per million tokens for input and output"               |

### Core Features

| Topic             | URL                                                                          | Extraction Prompt                                                                      |
| ----------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Extended Thinking | `https://platform.claude.com/docs/en/build-with-claude/extended-thinking.md` | "Extract extended thinking parameters, budget_tokens requirements, and usage examples" |
| Adaptive Thinking | `https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking.md` | "Extract adaptive thinking setup, effort levels, and Claude Opus 4.7 usage examples"         |
| Effort Parameter  | `https://platform.claude.com/docs/en/build-with-claude/effort.md`            | "Extract effort levels, cost-quality tradeoffs, and interaction with thinking"        |
| Tool Use          | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview.md`  | "Extract tool definition schema, tool_choice options, and handling tool results"       |
| Streaming         | `https://platform.claude.com/docs/en/build-with-claude/streaming.md`         | "Extract streaming event types, SDK examples, and best practices"                      |
| Prompt Caching    | `https://platform.claude.com/docs/en/build-with-claude/prompt-caching.md`    | "Extract cache_control usage, pricing benefits, and implementation examples"           |

### Media & Files

| Topic       | URL                                                                    | Extraction Prompt                                                 |
| ----------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Vision      | `https://platform.claude.com/docs/en/build-with-claude/vision.md`      | "Extract supported image formats, size limits, and code examples" |
| PDF Support | `https://platform.claude.com/docs/en/build-with-claude/pdf-support.md` | "Extract PDF handling capabilities, limits, and examples"         |

### API Operations

| Topic            | URL                                                                         | Extraction Prompt                                                                                       |
| ---------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Batch Processing | `https://platform.claude.com/docs/en/build-with-claude/batch-processing.md` | "Extract batch API endpoints, request format, and polling for results"                                  |
| Files API        | `https://platform.claude.com/docs/en/build-with-claude/files.md`            | "Extract file upload, download, and referencing in messages, including supported types and beta header" |
| Token Counting   | `https://platform.claude.com/docs/en/build-with-claude/token-counting.md`   | "Extract token counting API usage and examples"                                                         |
| Rate Limits      | `https://platform.claude.com/docs/en/api/rate-limits.md`                    | "Extract current rate limits by tier and model"                                                         |
| Errors           | `https://platform.claude.com/docs/en/api/errors.md`                         | "Extract HTTP error codes, meanings, and retry guidance"                                                |

### Tools

| Topic          | URL                                                                                    | Extraction Prompt                                                                        |
| -------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Code Execution | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool.md` | "Extract code execution tool setup, file upload, container reuse, and response handling" |
| Computer Use   | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use.md`        | "Extract computer use tool setup, capabilities, and implementation examples"             |
| Bash Tool      | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/bash-tool.md`           | "Extract bash tool schema, reference implementation, and security considerations"        |
| Text Editor    | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool.md`    | "Extract text editor tool commands, schema, and reference implementation"                |
| Memory Tool    | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool.md`         | "Extract memory tool commands, directory structure, and implementation patterns"         |
| Tool Search    | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool.md`    | "Extract tool search setup, when to use, and cache interaction"                          |
| Programmatic Tool Calling | `https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling.md` | "Extract PTC setup, script execution model, and tool invocation from code"    |
| Skills         | `https://platform.claude.com/docs/en/agents-and-tools/skills.md`                       | "Extract skill folder structure, SKILL.md format, and loading behavior"                  |

### Advanced Features

| Topic              | URL                                                                           | Extraction Prompt                                   |
| ------------------ | ----------------------------------------------------------------------------- | --------------------------------------------------- |
| Structured Outputs | `https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md` | "Extract output_config.format usage and schema enforcement"                           |
| Compaction         | `https://platform.claude.com/docs/en/build-with-claude/compaction.md`         | "Extract compaction setup, trigger config, and streaming with compaction"             |
| Context Editing    | `https://platform.claude.com/docs/en/build-with-claude/context-editing.md`    | "Extract context editing thresholds, what gets cleared, and configuration"            |
| Citations          | `https://platform.claude.com/docs/en/build-with-claude/citations.md`          | "Extract citation format and implementation"        |
| Context Windows    | `https://platform.claude.com/docs/en/build-with-claude/context-windows.md`    | "Extract context window sizes and token management" |

### Managed Agents

Use these when a managed-agents binding, behavior, or wire-level detail isn't covered in the cached `shared/managed-agents-*.md` concept files or in `{lang}/managed-agents/README.md`.

| Topic                 | URL                                                                              | Extraction Prompt                                                                               |
| --------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Overview              | `https://platform.claude.com/docs/en/managed-agents/overview.md`                 | "Extract the high-level architecture and how agents/sessions/environments/vaults fit together" |
| Quickstart            | `https://platform.claude.com/docs/en/managed-agents/quickstart.md`               | "Extract the minimal end-to-end agent → environment → session → stream code path"              |
| Agent Setup           | `https://platform.claude.com/docs/en/managed-agents/agent-setup.md`              | "Extract agent create/update/list-versions/archive lifecycle and parameters"                   |
| Define Outcomes       | `https://platform.claude.com/docs/en/managed-agents/define-outcomes.md`          | "Extract outcome definitions, evaluation hooks, and success criteria configuration"             |
| Sessions              | `https://platform.claude.com/docs/en/managed-agents/sessions.md`                 | "Extract session lifecycle, status transitions, idle/terminated semantics, and resume rules"    |
| Environments          | `https://platform.claude.com/docs/en/managed-agents/environments.md`             | "Extract environment config (cloud/networking), management endpoints, and reuse model"          |
| Events and Streaming  | `https://platform.claude.com/docs/en/managed-agents/events-and-streaming.md`     | "Extract event stream types, stream-first ordering, reconnect/dedupe, and steering patterns"    |
| Tools                 | `https://platform.claude.com/docs/en/managed-agents/tools.md`                    | "Extract built-in toolset, custom tool definitions, and tool result wire format"                |
| Files                 | `https://platform.claude.com/docs/en/managed-agents/files.md`                    | "Extract file upload, mount paths, session resources, and listing/downloading session outputs"  |
| Permission Policies   | `https://platform.claude.com/docs/en/managed-agents/permission-policies.md`      | "Extract permission policy types (allow/deny/confirm) and per-tool config"                     |
| Multi-Agent           | `https://platform.claude.com/docs/en/managed-agents/multi-agent.md`              | "Extract multi-agent composition patterns, sub-agent invocation, and result handoff"            |
| Observability         | `https://platform.claude.com/docs/en/managed-agents/observability.md`            | "Extract logging, tracing, and usage telemetry exposed by managed agents"                       |
| GitHub                | `https://platform.claude.com/docs/en/managed-agents/github.md`                   | "Extract github_repository resource shape, multi-repo mounting, and token rotation"             |
| MCP Connector         | `https://platform.claude.com/docs/en/managed-agents/mcp-connector.md`            | "Extract MCP server declaration on agents and vault-based credential injection at session"     |
| Vaults                | `https://platform.claude.com/docs/en/managed-agents/vaults.md`                   | "Extract vault create, credential add/rotate, OAuth refresh shape, and archive"                 |
| Skills                | `https://platform.claude.com/docs/en/managed-agents/skills.md`                   | "Extract skill packaging and loading model for managed agents"                                  |
| Memory                | `https://platform.claude.com/docs/en/managed-agents/memory.md`                   | "Extract memory resource shape, scoping, and lifecycle"                                         |
| Onboarding            | `https://platform.claude.com/docs/en/managed-agents/onboarding.md`               | "Extract first-run setup, prerequisites, and account/region requirements"                      |
| Cloud Containers      | `https://platform.claude.com/docs/en/managed-agents/cloud-containers.md`         | "Extract cloud container runtime, image config, and network/storage knobs"                     |
| Migration             | `https://platform.claude.com/docs/en/managed-agents/migration.md`                | "Extract migration paths from earlier APIs/preview shapes to GA managed agents"                 |

### Anthropic CLI

The `ant` CLI provides terminal access to the Claude API. Every API resource is exposed as a subcommand. It is one convenient way to create agents, environments, sessions, and other resources from version-controlled YAML, and to inspect responses interactively.

| Topic         | URL                                                     | Extraction Prompt                                                                                  |
| ------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Anthropic CLI | `https://platform.claude.com/docs/en/api/sdks/cli.md`   | "Extract CLI install, authentication, command structure, and the beta:agents/environments/sessions commands" |

---

## Claude API SDK Repositories

WebFetch these when a binding (class, method, namespace, field) isn't covered in the cached `{lang}/` skill files or in the managed-agents docs above. The SDKs include beta managed-agents support for `/v1/agents`, `/v1/sessions`, `/v1/environments`, and related resources — search the repo for `BetaManagedAgents`, `beta.agents`, `beta.sessions`, or the equivalent namespace for that language.

| SDK        | URL                                                      | Extraction Prompt                                                                                                       |
| ---------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Python     | `https://github.com/anthropics/anthropic-sdk-python`     | "Extract beta managed-agents namespaces, classes, and method signatures (`client.beta.agents`, `client.beta.sessions`)" |
| TypeScript | `https://github.com/anthropics/anthropic-sdk-typescript` | "Extract beta managed-agents namespaces, classes, and method signatures (`client.beta.agents`, `client.beta.sessions`)" |
| Java       | `https://github.com/anthropics/anthropic-sdk-java`       | "Extract beta managed-agents classes, builders, and method signatures (`client.beta().agents()`, `BetaManagedAgents*`)" |
| Go         | `https://github.com/anthropics/anthropic-sdk-go`         | "Extract beta managed-agents types and method signatures (`client.Beta.Agents`, `BetaManagedAgents*` event types)"      |
| Ruby       | `https://github.com/anthropics/anthropic-sdk-ruby`       | "Extract beta managed-agents methods and parameter shapes (`client.beta.agents`, `client.beta.sessions`)"               |
| C#         | `https://github.com/anthropics/anthropic-sdk-csharp`     | "Extract beta managed-agents classes and method signatures (NuGet package, `BetaManagedAgents*` types)"                 |
| PHP        | `https://github.com/anthropics/anthropic-sdk-php`        | "Extract beta managed-agents classes and method signatures (`$client->beta->agents`, `BetaManagedAgents*` params)"      |

---

## Fallback Strategy

If WebFetch fails (network issues, URL changed):

1. Use cached content from the language-specific files (note the cache date)
2. Inform user the data may be outdated
3. Suggest they check platform.claude.com or the GitHub repos directly

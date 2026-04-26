# Managed Agents — Overview

Managed Agents provisions a container per session as the agent's workspace. The agent loop runs on Anthropic's orchestration layer; the container is where the agent's *tools* execute — bash commands, file operations, code. You create a persisted **Agent** config (model, system prompt, tools, MCP servers, skills), then start **Sessions** that reference it. The session streams events back to you; you send user messages and tool results in.

## ⚠️ THE MANDATORY FLOW: Agent (once) → Session (every run)

**Why agents are separate objects: versioning.** An agent is a persisted, versioned config — every update creates a new immutable version, and sessions pin to a version at creation time. This lets you iterate on the agent (tweak the prompt, add a tool) without breaking sessions already running, roll back if a change regresses, and A/B test versions side-by-side. None of that works if you `agents.create()` fresh on every run.

Every session references a pre-created `/v1/agents` object. Create the agent once, store the ID, and reuse it across runs.

| Step | Call | Frequency |
|---|---|---|
| 1 | `POST /v1/agents` — `model`, `system`, `tools`, `mcp_servers`, `skills` live here | **ONCE.** Store `agent.id` **and** `agent.version`. |
| 2 | `POST /v1/sessions` — `agent: "agent_abc123"` or `{type: "agent", id, version}` | **Every run.** String shorthand uses latest version. |

If you're about to write `sessions.create()` with `model`, `system`, or `tools` on the session body — **stop**. Those fields live on `agents.create()`. The session takes a *pointer* only.

**When generating code, separate setup from runtime.** `agents.create()` belongs in a setup script (or a guarded `if agent_id is None:` block), not at the top of the hot path. If the user's code calls `agents.create()` on every invocation, they're accumulating orphaned agents and paying the create latency for nothing. The correct shape is: create once → persist the ID (config file, env var, secrets manager) → every run loads the ID and calls `sessions.create()`.

**To change the agent's behavior, use `POST /v1/agents/{id}` — don't create a new one.** Each update bumps the version; running sessions keep their pinned version, new sessions get the latest (or pin explicitly via `{type: "agent", id, version}`). See `shared/managed-agents-core.md` → Agents → Versioning.

## Beta Headers

Managed Agents is in beta. The SDK sets required beta headers automatically:

| Beta Header                    | What it enables                                      |
| ------------------------------ | ---------------------------------------------------- |
| `managed-agents-2026-04-01`    | Agents, Environments, Sessions, Events, Session Resources, Vaults, Credentials |
| `skills-2025-10-02`            | Skills API (for managing custom skill definitions)   |
| `files-api-2025-04-14`         | Files API for file uploads                           |

**Which beta header goes where:** The SDK sets `managed-agents-2026-04-01` automatically on `client.beta.{agents,environments,sessions,vaults}.*` calls, and `files-api-2025-04-14` / `skills-2025-10-02` automatically on `client.beta.files.*` / `client.beta.skills.*` calls. You do NOT need to add the Skills or Files beta header when calling Managed Agents endpoints. **Exception — session-scoped file listing:** `client.beta.files.list({scope_id: session.id})` is a Files endpoint that takes a Managed Agents parameter, so it needs **both** headers. Pass `betas: ["managed-agents-2026-04-01"]` explicitly on that call (the SDK adds the Files header; you add the Managed Agents one). See `shared/managed-agents-environments.md` → Session outputs.


## Reading Guide

| User wants to...                       | Read these files                                        |
| -------------------------------------- | ------------------------------------------------------- |
| **Get started from scratch / "help me set up an agent"** | `shared/managed-agents-onboarding.md` — guided interview (WHERE→WHO→WHAT→WATCH), then emit code |
| Understand how the API works           | `shared/managed-agents-core.md`                         |
| See the full endpoint reference        | `shared/managed-agents-api-reference.md`                |
| **Create an agent** (required first step) | `shared/managed-agents-core.md` (Agents section) + language file |
| Update/version an agent                | `shared/managed-agents-core.md` (Agents → Versioning) — update, don't re-create |
| Create a session                       | `shared/managed-agents-core.md` + `{lang}/managed-agents/README.md` |
| Configure tools and permissions        | `shared/managed-agents-tools.md`                        |
| Set up MCP servers                     | `shared/managed-agents-tools.md` (MCP Servers section)  |
| Stream events / handle tool_use        | `shared/managed-agents-events.md` + language file       |
| Set up environments                    | `shared/managed-agents-environments.md` + language file |
| Upload files / attach repos            | `shared/managed-agents-environments.md` (Resources)     |
| Store MCP credentials                  | `shared/managed-agents-tools.md` (Vaults section)       |
| Call a non-MCP API / CLI that needs a secret | `shared/managed-agents-client-patterns.md` Pattern 9 — no container env vars; vaults are MCP-only; keep the secret host-side via a custom tool |

## Common Pitfalls

- **Agent FIRST, then session — NO EXCEPTIONS** — the session's `agent` field accepts **only** a string ID or `{type: "agent", id, version}`. `model`, `system`, `tools`, `mcp_servers`, `skills` are **top-level fields on `POST /v1/agents`**, never on `sessions.create()`. If the user hasn't created an agent, that is step zero of every example.
- **Agent ONCE, not every run** — `agents.create()` is a setup step. Store the returned `agent_id` and reuse it; don't call `agents.create()` at the top of your hot path. If the agent's config needs to change, `POST /v1/agents/{id}` — each update creates a new version, and sessions can pin to a specific version for reproducibility.
- **MCP auth goes through vaults** — the agent's `mcp_servers` array declares `{type, name, url}` only (no auth). Credentials live in vaults (`client.beta.vaults.credentials.create`) and attach to sessions via `vault_ids`. Anthropic auto-refreshes OAuth tokens using the stored refresh token.
- **Stream to get events** — `GET /v1/sessions/{id}/events/stream` is the primary way to receive agent output in real-time.
- **SSE stream has no replay — reconnect with consolidation** — if the stream drops while a `agent.tool_use`, `agent.mcp_tool_use`, or `agent.custom_tool_use` is pending resolution (`user.tool_confirmation` for the first two, `user.custom_tool_result` for the last one), the session deadlocks (client disconnects → session idles → reconnect happens → no client resolution happens). On every (re)connect: open stream with `GET /v1/sessions/{id}/events/stream` , fetch `GET /v1/sessions/{id}/events`, dedupe by event ID, then proceed. See `shared/managed-agents-events.md` → Reconnecting after a dropped stream.
- **Don't trust HTTP-library timeouts as wall-clock caps** — `requests` `timeout=(c, r)` and `httpx.Timeout(n)` are *per-chunk* read timeouts; they reset every byte, so a trickling connection can block indefinitely. For a hard deadline on raw-HTTP polling, track `time.monotonic()` at the loop level and bail explicitly. Prefer the SDK's `sessions.events.stream()` / `session.events.list()` over hand-rolled HTTP. See `shared/managed-agents-events.md` → Receiving Events.
- **Messages queue** — you can send events while the session is `running` or `idle`; they're processed in order. No need to wait for a response before sending the next message.
- **Cloud environments only** — `config.type: "cloud"` is the only supported environment type.
- **Archive is permanent on every resource** — archiving an agent, environment, session, vault, or credential makes it read-only with no unarchive. For agents and environments specifically, archived resources cannot be referenced by new sessions (existing sessions continue). Do not call `.archive()` on a production agent or environment as cleanup — **always confirm with the user before archiving**.
# Managed Agents — Core Concepts

## Architecture

Managed Agents is built around four core concepts:

| Concept | Endpoint | What it is |
|---|---|---|
| **Agent** | `/v1/agents` | A persisted, versioned object defining the agent's capabilities and persona: model, system prompt, tools, MCP servers, skills. **Must be created before starting a session.** See the Agents section below. |
| **Session** | `/v1/sessions` | A stateful interaction with an agent. References a pre-created agent by ID + an environment + initial instructions. Produces an event stream. |
| **Environment** | `/v1/environments` | A template defining the configuration for container provisioning. |
| **Container** | N/A | An isolated compute instance where the agent's **tools** execute (bash, file ops, code). The agent loop does not run here — it runs on Anthropic's orchestration layer and acts on the container via tool calls. |

```
                       ┌─────────────────────────────────────┐
                       │  Anthropic orchestration layer      │
Agent (config) ───────▶│  (agent loop: Claude + tool calls)  │
                       └──────────────┬──────────────────────┘
                                      │ tool calls
                                      ▼
Environment (template) ──▶ Container (tool execution workspace)
                                 │
                         Session ─┤
                                 ├── Resources (files, repos — mounted at startup)
                                 ├── Vault IDs (MCP credential references)
                                 └── Conversation (event stream in/out)
```

> **Agent creation is a prerequisite.** Sessions reference a pre-created agent by ID — `model`/`system`/`tools` live on the agent object, never on the session. Every flow starts with `POST /v1/agents`.

---

## Session Lifecycle

```
rescheduling → running ↔ idle → terminated
```

| Status         | Description                                                        |
| -------------- | ------------------------------------------------------------------ |
| `idle` | Agent has finished the current task, and is awaiting input. It's either waiting for input to continue working via a `user.message` or blocked awaiting a `user.custom_tool_result` or `user.tool_confirmation`. The `stop_reason` attached contains more information about why the Agent has stopped working. |
| `running` | Session has starting running, and the Agent is actively doing work. |
| `rescheduling` | Session is (re)scheduling after a retryable error has occurred, ready to be picked up by the orchestration system. |
| `terminated` | Session has terminated, entering an irreversible and unusable state.  |

- Events can be sent when the session is `running` or `idle`. Messages are queued and processed in order.
- The agent transitions `idle → running` when it receives a new event, then back to `idle` when done.
- Errors surface as `session.error` events in the stream, not as a status value.

### Built-in session features

- **Context compaction** — if you approach max context, the API automatically condenses session history to keep the interaction going
- **Prompt caching** — historical repeated tokens are cached, reducing processing time and cost
- **Extended thinking** — on by default, returned as `agent.thinking` events

### Session operations

| Operation | Notes |
|---|---|
| List / fetch | Paginated list or single resource by ID |
| Update | Only `title` is updatable |
| Archive | Session becomes **read-only**. Not reversible. |
| Delete | Permanently deletes session, event history, container, and checkpoints. |

---

## Sessions

A session is a running agent instance inside an environment.

### Session Object

Key fields returned by the API:

| Field           | Type     | Description                                         |
| --------------- | -------- | --------------------------------------------------- |
| `type` | string | Always `"session"` |
| `id` | string | Unique session ID |
| `title` | string | Human-readable title |
| `status` | string | `idle`, `running`, `rescheduling`, `terminated` |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `archived_at` | string | ISO 8601 timestamp (nullable) |
| `environment_id` | string | Environment ID |
| `agent` | object | Agent configuration |
| `resources` | array | Attached files and repos |
| `metadata` | object | User-provided key-value pairs (max 8 keys) |
| `usage` | object | Token usage statistics |

### Creating a session

**A session is meaningless without an agent.** Sessions reference a pre-created agent by ID. Create the agent first via `agents.create()`, then reference it:

```ts
// 1. Create the agent (reusable, versioned)
const agent = await client.beta.agents.create(
  {
    name: "Coding Assistant",
    model: "claude-opus-4-7",
    system: "You are a helpful coding agent.",
    tools: [{ type: "agent_toolset_20260401"}],
  },
);

// 2. Start a session that references it
const session = await client.beta.sessions.create(
  {
    agent: agent.id,  // string shorthand → latest version. Or: { type: "agent", id: agent.id, version: agent.version }
    environment_id: environmentId,
    title: "Hello World Session",
  },
);
```

**Session creation parameters:**

| Field           | Type     | Required | Description                                    |
| --------------- | -------- | -------- | ---------------------------------------------- |
| `agent`         | string or object | **Yes** | String shorthand `"agent_abc123"` (latest version) or `{type: "agent", id, version}` |
| `environment_id`| string   | **Yes**  | Environment ID                                 |
| `title`         | string   | No       | Human-readable name (appears in logs/dashboards) |
| `resources`     | array    | No       | Files or GitHub repos, mounted to the container at startup |
| `vault_ids`     | array    | No       | Vault IDs (`vlt_*`) — MCP credentials with auto-refresh. See `shared/managed-agents-tools.md` → Vaults. |
| `metadata`      | object   | No       | User-provided key-value pairs                  |

**Agent configuration fields** (passed to `agents.create()`, not `sessions.create()`):

| Field         | Type     | Required | Description                                    |
| ------------- | -------- | -------- | ---------------------------------------------- |
| `name`        | string   | **Yes**  | Human-readable name (1-256 chars)              |
| `model`       | string or object | **Yes** | Claude model ID (bare string, or `{id, speed}` object). All Claude 4.5+ models supported. |
| `system`      | string   | No       | System prompt — defines the agent's behavior (up to 100K chars) |
| `tools`       | array    | No       | Encompasses three kinds: (1) pre-built Claude Agent tools (`agent_toolset_20260401`), (2) MCP tools (`mcp_toolset`), and (3) custom client-side tools. Max 128. |
| `mcp_servers` | array    | No       | MCP server connections — standardized third-party capabilities (e.g. GitHub, Asana). Max 20, unique names. See `shared/managed-agents-tools.md` → MCP Servers. |
| `skills`      | array    | No       | Customized "best-practices" context with progressive disclosure. Max 64. See `shared/managed-agents-tools.md` → Skills. |
| `description` | string   | No       | Description of the agent (up to 2048 chars)    |
| `metadata`    | object   | No       | Arbitrary key-value pairs (max 16, keys ≤64 chars, values ≤512 chars) |

---

## Agents

**This is where every Managed Agents flow begins.** The agent object is a persisted, versioned configuration — you create it once, then reference it by ID every time you start a session. No agent → no session.

### Agent Object

The API is **flat** — `model`, `system`, `tools` etc. are top-level fields, not wrapped in an `agent:{}` sub-object.

| Field              | Type     | Required | Description                                        |
| ------------------ | -------- | -------- | -------------------------------------------------- |
| `name`             | string   | Yes      | Human-readable name                                |
| `model`            | string   | Yes      | Claude model ID                                    |
| `system`           | string   | No       | System prompt                                      |
| `tools`            | array    | No       | Agent toolset / MCP toolset / custom tools         |
| `mcp_servers`      | array    | No       | MCP server connections                             |
| `skills`           | array    | No       | Skill references (max 64)                          |
| `description`      | string   | No       | Description of the agent                           |
| `metadata`         | object   | No       | Arbitrary key-value pairs                          |

### Lifecycle: create once, run many, update in place

The agent is a **persistent resource**, not a per-run parameter. The intended pattern:

```
┌─ setup (once) ─────────┐     ┌─ runtime (every invocation) ─┐
│ agents.create()        │     │ sessions.create(             │
│   → store agent_id     │ ──→ │   agent={type:..., id: ID}   │
│     in config/env/db   │     │ )                            │
└────────────────────────┘     └──────────────────────────────┘
```

**Anti-pattern:** calling `agents.create()` at the top of every script run. This accumulates orphaned agent objects, pays create latency on every invocation, and defeats the versioning model. If you see `agents.create()` in a function that's called per-request or per-cron-tick, that's wrong — hoist it to one-time setup and persist the ID.

### Versioning

Each `POST /v1/agents/{id}` (update) creates a new immutable version (numeric timestamp, e.g. `1772585501101368014`). The agent's history is append-only — you can't edit a past version.

**Why version:**
- **Reproducibility** — pin a session to a known-good config: `{type: "agent", id, version: 3}`
- **Safe iteration** — update the agent without breaking sessions already running on the old version
- **Rollback** — if a new system prompt regresses, pin new sessions back to the prior version while you debug

**`version` is optional.** Omit it (or use the string shorthand `agent="agent_abc123"`) to get the latest version at session-creation time. Pass it explicitly (`{type: "agent", id, version: N}`) to pin for reproducibility.

**Getting the version to pin:** `agents.create()` and `agents.update()` both return `version` in the response. Store it alongside `agent_id`. To fetch the current latest for an existing agent: `GET /v1/agents/{id}` → `.version`.

**When to update vs create new:** Update (`POST /v1/agents/{id}`) when it's conceptually the same agent with tweaked behavior (better prompt, extra tool). Create a new agent when it's a different persona/purpose. Rule of thumb: if you'd give it the same `name`, update.

### Agent Endpoints

| Operation        | Method   | Path                                  |
| ---------------- | -------- | ------------------------------------- |
| Create           | `POST`   | `/v1/agents`                          |
| List             | `GET`    | `/v1/agents`                          |
| Get              | `GET`    | `/v1/agents/{id}`                     |
| Update           | `POST`   | `/v1/agents/{id}`                     |
| Archive          | `POST`   | `/v1/agents/{id}/archive`             |

> ⚠️ **Archive is permanent.** Archiving makes the agent read-only: existing sessions continue to run, but **new sessions cannot reference it**, and there is no unarchive. Since agents have no `delete`, this is the terminal lifecycle state. Never archive a production agent as routine cleanup — confirm with the user first.

### Using an Agent in a Session

Reference the agent by string ID (latest version) or by object with an explicit version:

```python
# String shorthand — uses the agent's latest version
session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=environment_id,
)

# Or pin to a specific version (int)
session = client.beta.sessions.create(
    agent={"type": "agent", "id": agent.id, "version": agent.version},
    environment_id=environment_id,
)
```

# Managed Agents — Common Client Patterns

Patterns you'll write on the client side when driving a Managed Agent session, grounded in working SDK examples.

Code samples are TypeScript — Python and cURL follow the same shape; see `python/managed-agents/README.md` and `curl/managed-agents.md` for equivalents.

---

## 1. Lossless stream reconnect

**Problem:** SSE has no replay. If the connection drops mid-session, a naive reconnect re-opens the stream from "now" and you silently miss every event emitted in between.

**Solution:** on reconnect, fetch the full event history via `events.list()` *before* consuming the live stream, and dedupe on event ID as the live stream catches up.

```ts
const seenEventIds = new Set<string>()
const stream = await client.beta.sessions.events.stream(session.id)

// Stream is now open and buffering server-side. Read history first.
for await (const event of client.beta.sessions.events.list(session.id)) {
  seenEventIds.add(event.id)
  handle(event)
}

// Tail the live stream. Dedupe only gates handle() — terminal checks must run
// even for already-seen events, or a terminal event that was in the history
// response gets skipped by `continue` and the loop never exits.
for await (const event of stream) {
  if (!seenEventIds.has(event.id)) {
    seenEventIds.add(event.id)
    handle(event)
  }
  if (event.type === 'session.status_terminated') break
  if (event.type === 'session.status_idle' && event.stop_reason.type !== 'requires_action') break
}
```

---

## 2. `processed_at` — queued vs processed

Every event on the stream carries `processed_at` (ISO 8601). For client-sent events (`user.message`, `user.interrupt`, `user.tool_confirmation`, `user.custom_tool_result`) it's `null` when the event has been queued but not yet picked up by the agent, and populated once the agent processes it. The same event appears on the stream twice — once with `processed_at: null`, once with a timestamp.

```ts
for await (const event of stream) {
  if (event.type === 'user.message') {
    if (event.processed_at == null) onQueued(event.id)
    else onProcessed(event.id, event.processed_at)
  }
}
```

Use this to drive pending → acknowledged UI state for anything you send. How you map a locally-rendered optimistic message to the server-assigned `event.id` is application-specific (typically via the return value of `events.send()` or FIFO ordering).

---

## 3. Interrupt a running session

Send `user.interrupt` as a normal event. The session keeps running until it reaches a safe boundary, then goes idle.

```ts
await client.beta.sessions.events.send(session.id, {
  events: [{ type: 'user.interrupt' }],
})

// Drain until the session is truly done — see Pattern 5 for the full gate.
for await (const event of stream) {
  if (event.type === 'session.status_terminated') break
  if (
    event.type === 'session.status_idle' &&
    event.stop_reason.type !== 'requires_action'
  ) break
}
```

Reference: `interrupt.ts` — sends the interrupt the moment it sees `span.model_request_start`, drains to idle, then verifies via `sessions.retrieve()`.

---

## 4. `tool_confirmation` round-trip

When the agent has `permission_policy: { type: 'always_ask' }`, any call to that tool fires an `agent.tool_use` event with `evaluated_permission === 'ask'` and the session goes idle waiting for a decision. Respond with `user.tool_confirmation`.

```ts
for await (const event of stream) {
  if (event.type === 'agent.tool_use' && event.evaluated_permission === 'ask') {
    await client.beta.sessions.events.send(session.id, {
      events: [{
        type: 'user.tool_confirmation',
        tool_use_id: event.id,         // not a toolu_ id — use event.id
        result: 'allow',               // or 'deny'
        // deny_message: '...',        // optional, only with result: 'deny'
      }],
    })
  }
}
```

Key points:
- `tool_use_id` is `event.id` (typically `sevt_...`), **not** a `toolu_...` ID.
- `result` is `'allow' | 'deny'`. Use `deny_message` to tell the model *why* you denied — it gets surfaced back to the agent.
- Multiple pending tools: respond once per `agent.tool_use` event with `evaluated_permission === 'ask'`.

Reference: `tool-permissions.ts`.

---

## 5. Correct idle-break gate

Do not break on `session.status_idle` alone. The session goes idle transiently — e.g. between parallel tool executions, while waiting for a `user.tool_confirmation`, or while awaiting a `user.custom_tool_result`. Break when idle with a terminal `stop_reason`, or on `session.status_terminated`.

```ts
for await (const event of stream) {
  handle(event)
  if (event.type === 'session.status_terminated') break
  if (event.type === 'session.status_idle') {
    if (event.stop_reason.type === 'requires_action') continue // waiting on you — handle it
    break // end_turn or retries_exhausted — both terminal
  }
}
```

`stop_reason.type` values on `session.status_idle`:
- `requires_action` — agent is waiting on a client-side event (tool confirmation, custom tool result). Handle it, don't break.
- `retries_exhausted` — terminal failure. Break, then check `sessions.retrieve()` for the error state.
- `end_turn` — normal completion.

---

## 6. Post-idle status-write race

The SSE stream emits `session.status_idle` slightly before the session's queryable status reflects it. Clients that break on idle and immediately call `sessions.delete()` or `sessions.archive()` will intermittently 400 with "cannot delete/archive while running."

Poll before cleanup:

```ts
let s
for (let i = 0; i < 10; i++) {
  s = await client.beta.sessions.retrieve(session.id)
  if (s.status !== 'running') break
  await new Promise(r => setTimeout(r, 200))
}
if (s?.status !== 'running') {
  await client.beta.sessions.archive(session.id)
} // else: still running after 2s — don't archive, let it settle or escalate
```

---

## 7. Stream-first, then send

Always open the stream **before** sending the kickoff event. Otherwise the agent may process the event and emit the first events before your consumer is attached, and you'll miss them.

```ts
const stream = await client.beta.sessions.events.stream(session.id)
await client.beta.sessions.events.send(session.id, {
  events: [{ type: 'user.message', content: [{ type: 'text', text: 'Hello' }] }],
})
for await (const event of stream) { /* ... */ }
```

The `Promise.all([stream, send])` shape works too, but stream-first is simpler and has the same effect — the stream starts buffering the moment it's opened.

---

## 8. File-mount gotchas

**The mounted resource has a different `file_id` than the file you uploaded.** Session creation makes a session-scoped copy.

```ts
const uploaded = await client.beta.files.upload({ file, purpose: 'agent_resource' })
// uploaded.id         → the original file
const session = await client.beta.sessions.create({
  /* ... */
  resources: [{ type: 'file', file_id: uploaded.id, mount_path: '/workspace/data.csv' }],
})
// session.resources[0].file_id !== uploaded.id  ← different IDs
```

Delete the original via `files.delete(uploaded.id)`; the session-scoped copy is garbage-collected with the session. `mount_path` must be absolute — see `shared/managed-agents-environments.md`.

---

## 9. Secrets for non-MCP APIs and CLIs — keep them host-side via custom tools

**Problem:** you want the agent to call a third-party API or run a CLI that needs a secret (API key, token, service-account credential), but there is currently no way to set environment variables inside the session container, and vaults currently hold MCP credentials only — they are not exposed to the container's shell. So `curl`, installed CLIs, or SDK clients running via the `bash` tool have no first-class place to read a secret from.

**Solution:** move the authenticated call to your side. Declare a custom tool on the agent; when the agent emits `agent.custom_tool_use`, your orchestrator (the process reading the SSE stream) executes the call with its own credentials and responds with `user.custom_tool_result`. The container never sees the key.

```ts
// Agent template: declare the tool, no credentials
tools: [{ type: 'custom', name: 'linear_graphql', input_schema: { /* query, vars */ } }]

// Orchestrator: handle the call with host-side creds
for await (const event of stream) {
  if (event.type === 'agent.custom_tool_use' && event.name === 'linear_graphql') {
    const result = await linear.request(event.input.query, event.input.vars) // host's key
    await client.beta.sessions.events.send(session.id, {
      events: [{ type: 'user.custom_tool_result', tool_use_id: event.id, result }],
    })
  }
}
```

Same shape works for `gh` CLI, local eval scripts, or anything else that needs host-side auth or binaries.

**Security note:** this does not expose a public endpoint. `agent.custom_tool_use` arrives on the SSE stream your orchestrator already holds open with your Anthropic API key, and `user.custom_tool_result` goes back via `events.send()` under the same key. Your orchestrator is a client, not a server — nothing unauthenticated is listening.

**Do not embed API keys in the system prompt or user messages as a workaround.** Prompts and messages are stored in the session's event history, returned by `events.list()`, and included in compaction summaries — a secret placed there is durably persisted and readable via the API for the life of the session.
# Managed Agents — Endpoint Reference

All endpoints require `x-api-key` and `anthropic-version: 2023-06-01` headers. Managed Agents endpoints additionally require the `anthropic-beta` header.

## Beta Headers

```
anthropic-beta: managed-agents-2026-04-01
```

The SDK adds this header automatically for all `client.beta.{agents,environments,sessions,vaults}.*` calls. Skills endpoints use `skills-2025-10-02`; Files endpoints use `files-api-2025-04-14`.

---

## SDK Method Reference

All resources are under the `beta` namespace. Python and TypeScript share identical method names.

| Resource | Python / TypeScript (`client.beta.*`) | Go (`client.Beta.*`) |
| --- | --- | --- |
| Agents | `agents.create` / `retrieve` / `update` / `list` / `archive` | `Agents.New` / `Get` / `Update` / `List` / `Archive` |
| Agent Versions | `agents.versions.list` | `Agents.Versions.List` |
| Environments | `environments.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Environments.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |
| Sessions | `sessions.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Sessions.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |
| Session Events | `sessions.events.list` / `send` / `stream` | `Sessions.Events.List` / `Send` / `StreamEvents` |
| Session Resources | `sessions.resources.add` / `retrieve` / `update` / `list` / `delete` | `Sessions.Resources.Add` / `Get` / `Update` / `List` / `Delete` |
| Vaults | `vaults.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Vaults.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |
| Credentials | `vaults.credentials.create` / `retrieve` / `update` / `list` / `delete` / `archive` | `Vaults.Credentials.New` / `Get` / `Update` / `List` / `Delete` / `Archive` |

**Naming quirks to watch for:**
- Agents have **no delete** — only `archive`. Archive is **permanent**: the agent becomes read-only, new sessions cannot reference it, and there is no unarchive. Confirm with the user before archiving a production agent. Environments, Sessions, Vaults, and Credentials have both `delete` and `archive`; Session Resources, Files, and Skills are `delete`-only.
- Session resources use `add` (not `create`).
- Go's event stream is `StreamEvents` (not `Stream`).

**Agent shorthand:** `agent` on session create accepts either a bare string (`agent="agent_abc123"` — uses latest version) or the full reference object (`{type: "agent", id: "agent_abc123", version: 123}`).

**Model shorthand:** `model` on agent create accepts either a bare string (`model="claude-opus-4-7"` — uses `standard` speed) or the full config object (`{type: "model_config", id: "claude-opus-4-6", speed: "fast"}`). Note: `speed: "fast"` is only supported on Opus 4.6.

---

## Agents

**Step one of every flow.** Sessions require a pre-created agent — there is no inline agent config under `managed-agents-2026-04-01`.

| Method   | Path                                             | Operation        | Description                              |
| -------- | ------------------------------------------------ | ---------------- | ---------------------------------------- |
| `GET` | `/v1/agents` | ListAgents | List agents |
| `POST` | `/v1/agents` | CreateAgent | Create a saved agent configuration |
| `GET` | `/v1/agents/{agent_id}` | GetAgent | Get agent details |
| `POST` | `/v1/agents/{agent_id}` | UpdateAgent | Update agent configuration |
| `POST` | `/v1/agents/{agent_id}/archive` | ArchiveAgent | Archive an agent. Makes it **read-only**; existing sessions continue, new sessions cannot reference it. No unarchive — this is the terminal state. |
| `GET` | `/v1/agents/{agent_id}/versions` | ListAgentVersions | List agent versions |

## Sessions

| Method   | Path                                             | Operation        | Description                              |
| -------- | ------------------------------------------------ | ---------------- | ---------------------------------------- |
| `GET` | `/v1/sessions` | ListSessions | List sessions (paginated) |
| `POST` | `/v1/sessions` | CreateSession | Create a new session |
| `GET` | `/v1/sessions/{session_id}` | GetSession | Get session details |
| `POST` | `/v1/sessions/{session_id}` | UpdateSession | Update session metadata/title |
| `DELETE` | `/v1/sessions/{session_id}` | DeleteSession | Delete a session |
| `POST` | `/v1/sessions/{session_id}/archive` | ArchiveSession | Archive a session |

## Events

| Method   | Path                                             | Operation        | Description                              |
| -------- | ------------------------------------------------ | ---------------- | ---------------------------------------- |
| `GET` | `/v1/sessions/{session_id}/events` | ListEvents | List events (polling, paginated) |
| `POST` | `/v1/sessions/{session_id}/events` | SendEvents | Send events (user message, tool result) |
| `GET` | `/v1/sessions/{session_id}/events/stream` | StreamEvents | Stream events via SSE |

## Session Resources

| Method   | Path                                                    | Operation        | Description                              |
| -------- | ------------------------------------------------------- | ---------------- | ---------------------------------------- |
| `GET` | `/v1/sessions/{session_id}/resources` | ListResources | List resources attached to session |
| `POST` | `/v1/sessions/{session_id}/resources` | AddResource | Attach file or github_repository mount (SDK method: `add`, not `create`) |
| `GET` | `/v1/sessions/{session_id}/resources/{resource_id}` | GetResource | Get a single resource |
| `POST` | `/v1/sessions/{session_id}/resources/{resource_id}` | UpdateResource | Update resource |
| `DELETE` | `/v1/sessions/{session_id}/resources/{resource_id}` | DeleteResource | Remove resource from session |

## Environments

| Method   | Path                                                             | Operation            | Description                         |
| -------- | ---------------------------------------------------------------- | -------------------- | ----------------------------------- |
| `POST`   | `/v1/environments`                                     | CreateEnvironment    | Create environment                  |
| `GET`    | `/v1/environments`                                     | ListEnvironments     | List environments                   |
| `GET`    | `/v1/environments/{environment_id}`                    | GetEnvironment       | Get environment details             |
| `POST`   | `/v1/environments/{environment_id}`                    | UpdateEnvironment    | Update environment                  |
| `DELETE` | `/v1/environments/{environment_id}`                    | DeleteEnvironment    | Delete environment. Returns 204. |
| `POST`   | `/v1/environments/{environment_id}/archive`            | ArchiveEnvironment   | Archive environment. Makes it **read-only**; existing sessions continue, new sessions cannot reference it. No unarchive — this is the terminal state. |

## Vaults

Vaults store MCP credentials that Anthropic manages on your behalf — OAuth credentials with auto-refresh, or static bearer tokens. Attach to sessions via `vault_ids`. See `managed-agents-tools.md` §Vaults for the conceptual guide and credential shapes.

| Method   | Path                                             | Operation        | Description                              |
| -------- | ------------------------------------------------ | ---------------- | ---------------------------------------- |
| `POST`   | `/v1/vaults`                                     | CreateVault      | Create a vault                           |
| `GET`    | `/v1/vaults`                                     | ListVaults       | List vaults                              |
| `GET`    | `/v1/vaults/{vault_id}`                          | GetVault         | Get vault details                        |
| `POST`   | `/v1/vaults/{vault_id}`                          | UpdateVault      | Update vault                             |
| `DELETE` | `/v1/vaults/{vault_id}`                          | DeleteVault      | Delete vault                             |
| `POST`   | `/v1/vaults/{vault_id}/archive`                  | ArchiveVault     | Archive vault                            |

## Credentials

Credentials are individual secrets stored inside a vault.

| Method   | Path                                                              | Operation          | Description                  |
| -------- | ----------------------------------------------------------------- | ------------------ | ---------------------------- |
| `POST`   | `/v1/vaults/{vault_id}/credentials`                               | CreateCredential   | Create a credential          |
| `GET`    | `/v1/vaults/{vault_id}/credentials`                               | ListCredentials    | List credentials in vault    |
| `GET`    | `/v1/vaults/{vault_id}/credentials/{credential_id}`               | GetCredential      | Get credential metadata      |
| `POST`   | `/v1/vaults/{vault_id}/credentials/{credential_id}`               | UpdateCredential   | Update credential            |
| `DELETE` | `/v1/vaults/{vault_id}/credentials/{credential_id}`               | DeleteCredential   | Delete credential            |
| `POST`   | `/v1/vaults/{vault_id}/credentials/{credential_id}/archive`       | ArchiveCredential  | Archive credential           |

## Files

| Method   | Path                                             | Operation        | Description                              |
| -------- | ------------------------------------------------ | ---------------- | ---------------------------------------- |
| `POST`   | `/v1/files`                            | UploadFile       | Upload a file                            |
| `GET`    | `/v1/files`                            | ListFiles        | List files                               |
| `GET`    | `/v1/files/{file_id}`                  | GetFile          | Get file metadata (SDK method: `retrieve_metadata`) |
| `GET`    | `/v1/files/{file_id}/content`          | DownloadFile     | Download file content                    |
| `DELETE` | `/v1/files/{file_id}`                  | DeleteFile       | Delete a file                            |

## Skills

| Method   | Path                                                            | Operation          | Description                  |
| -------- | --------------------------------------------------------------- | ------------------ | ---------------------------- |
| `POST`   | `/v1/skills`                                          | CreateSkill        | Create a skill               |
| `GET`    | `/v1/skills`                                          | ListSkills         | List skills                  |
| `GET`    | `/v1/skills/{skill_id}`                               | GetSkill           | Get skill details            |
| `DELETE` | `/v1/skills/{skill_id}`                               | DeleteSkill        | Delete a skill               |
| `POST`   | `/v1/skills/{skill_id}/versions`                      | CreateVersion      | Create skill version         |
| `GET`    | `/v1/skills/{skill_id}/versions`                      | ListVersions       | List skill versions          |
| `GET`    | `/v1/skills/{skill_id}/versions/{version}`            | GetVersion         | Get skill version            |
| `DELETE` | `/v1/skills/{skill_id}/versions/{version}`            | DeleteVersion      | Delete skill version         |

---

## Request/Response Schema Quick Reference

### CreateAgent Request Body

**Always start here.** `model`, `system`, `tools`, `mcp_servers`, `skills` are top-level fields on this object — they do NOT go on the session.

```json
{
  "name": "string (required, 1-256 chars)",
  "model": "claude-opus-4-7 (required — bare string, or {id, speed} object)",
  "description": "string (optional, up to 2048 chars)",
  "system": "string (optional, up to 100,000 chars)",
  "tools": [
    { "type": "agent_toolset_20260401" }
  ],
  "skills": [
    { "type": "anthropic", "skill_id": "xlsx" },
    { "type": "custom", "skill_id": "skill_abc123", "version": "1" }
  ],
  "mcp_servers": [
    {
      "type": "url",
      "name": "github",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  ],
  "metadata": {
    "key": "value (max 16 pairs, keys ≤64 chars, values ≤512 chars)"
  }
}
```

> Limits: `tools` max 50, `skills` max 64, `mcp_servers` max 20 (unique names).

### CreateSession Request Body

```json
{
  "agent": "agent_abc123 (required — string shorthand for latest version, or {type: \"agent\", id, version} object)",
  "environment_id": "env_abc123 (required)",
  "title": "string (optional)",
  "resources": [
    {
      "type": "github_repository",
      "url": "https://github.com/owner/repo (required)",
      "authorization_token": "ghp_... (required)",
      "mount_path": "/workspace/repo (optional — defaults to /workspace/<repo-name>)",
      "checkout": { "type": "branch", "name": "main" }
    }
  ],
  "vault_ids": ["vlt_abc123 (optional — MCP credentials with auto-refresh)"],
  "metadata": {
    "key": "value"
  }
}
```

> The `agent` field accepts only a string ID or `{type: "agent", id, version}` — `model`/`system`/`tools` live on the agent, not here.
>
> **`checkout`** accepts `{type: "branch", name: "..."}` or `{type: "commit", sha: "..."}`. Omit for the repo's default branch.

### CreateEnvironment Request Body

```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "config": {
    "type": "cloud",
    "networking": {
      "type": "unrestricted | limited (union — see SDK types)"
    },
    "packages": { }
  },
  "metadata": { "key": "value" }
}
```

### SendEvents Request Body

```json
{
  "events": [
    {
      "type": "user.message",
      "content": [
        {
          "type": "text",
          "text": "Hello"
        }
      ]
    }
  ]
}
```

### Tool Result Event

```json
{
  "type": "user.custom_tool_result",
  "custom_tool_use_id": "sevt_abc123",
  "content": [{ "type": "text", "text": "Result data" }],
  "is_error": false
}
```

---

## Error Handling

Managed Agents endpoints use the standard Anthropic API error format. Errors are returned with an HTTP status code and a JSON body containing `type`, `error`, and `request_id`:

```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "message": "Description of what went wrong"
  },
  "request_id": "req_011CRv1W3XQ8XpFikNYG7RnE"
}
```

Include the `request_id` when reporting issues to Anthropic — it lets us trace the request end-to-end. The inner `error.type` is one of the following:

| Status | Error type | Description |
|---|---|---|
| 400 | `invalid_request_error` | The request was malformed or missing required parameters |
| 401 | `authentication_error` | Invalid or missing API key |
| 403 | `permission_error` | The API key doesn't have permission for this operation |
| 404 | `not_found_error` | The requested resource doesn't exist |
| 409 | `invalid_request_error` | The request conflicts with the resource's current state (e.g., sending to an archived session) |
| 413 | `request_too_large` | The request body exceeds the maximum allowed size |
| 429 | `rate_limit_error` | Too many requests — check rate limit headers for retry timing |
| 500 | `api_error` | An internal server error occurred |
| 529 | `overloaded_error` | The service is temporarily overloaded — retry with backoff |

Note that `409 Conflict` carries `error.type: "invalid_request_error"` (there is no separate `conflict_error` type); inspect both the HTTP status and the `message` to distinguish conflicts from other invalid requests.

---

## Rate Limits

Managed Agents endpoints have per-organization request-per-minute (RPM) limits, separate from your [Messages API token limits](https://platform.claude.com/docs/en/api/rate-limits). Model inference inside a session still draws from your organization's standard ITPM/OTPM limits.

| Endpoint group | Scope | RPM | Max concurrent |
|---|---|---|---|
| Create operations (Agents, Sessions, Vaults) | organization | 60 | — |
| All other operations (Agents, Sessions, Vaults) | organization | 600 | — |
| All operations (Environments) | organization | 60 | 5 |

Files and Skills endpoints use the standard tier-based [rate limits](https://platform.claude.com/docs/en/api/rate-limits).

When a limit is exceeded the API returns `429` with a `rate_limit_error` (see [Error Handling](#error-handling) for the response envelope) and a `retry-after` header indicating how many seconds to wait before retrying. The Anthropic SDK reads this header and retries automatically.
# Managed Agents — Environments & Resources

## Environments

Creating a session requires an `environment_id`. Environments are **reusable configuration templates** for spinning up containers in Anthropic's infrastructure — you might create different environments for different use cases (e.g. data visualization vs web development, with different package sets). Anthropic handles scaling, container lifecycle, and work orchestration.

**Environment names must be unique.** Creating an environment with an existing name returns 409.

### Networking

| Network Policy                  | Description                                                   |
| ------------------------------- | ------------------------------------------------------------- |
| `unrestricted`                  | Full egress (except legal blocklist)                          |
| `package_managers_and_custom`   | Package managers + custom `allowed_hosts`                      |

```json
{
  "networking": {
    "type": "package_managers_and_custom",
    "allowed_hosts": ["api.example.com"]
  }
}
```

**MCP caveat:** If using restricted networking, make sure `allowed_hosts` includes your MCP server domains. Otherwise the container can't reach them and tools silently fail.

### Creating an environment

The SDK adds `managed-agents-2026-04-01` automatically. TypeScript:

```ts
const env = await client.beta.environments.create({
  name: "my_env",
  config: {
    type: "cloud",
    networking: { type: "unrestricted" },
  },
});
```

### Environment CRUD

| Operation        | Method   | Path                                       | Notes |
| ---------------- | -------- | ------------------------------------------ | ----- |
| Create           | `POST`   | `/v1/environments`                         | |
| List             | `GET`    | `/v1/environments`                         | Paginated (`limit`, `after_id`, `before_id`) |
| Get              | `GET`    | `/v1/environments/{id}`                    | |
| Update           | `POST`   | `/v1/environments/{id}`                    | Changes apply only to **new** containers; existing sessions keep their original config |
| Delete           | `DELETE` | `/v1/environments/{id}`                    | Returns 204. |
| Archive          | `POST`   | `/v1/environments/{id}/archive`            | Makes it **read-only**; existing sessions continue, new sessions cannot reference it. No unarchive — terminal state. |

---

## Resources

Attach files and GitHub repositories to a session. **Session creation blocks until all resources are mounted** — the container won't go `running` until every file and repo is in place. Max **999 file resources** per session. Multiple GitHub repositories per session are supported.

### File Uploads (input — host → agent)

Upload a file first via the Files API, then reference by `file_id` + `mount_path`:

```ts
// 1. Upload
const file = await client.beta.files.upload({
  file: fs.createReadStream("data.csv"),
  purpose: "agent",
});

// 2. Attach as a session resource
const session = await client.beta.sessions.create({
  agent: agent.id,
  environment_id: envId,
  resources: [
    { type: "file", file_id: file.id, mount_path: "/workspace/data.csv" }
  ],
});
```

**`mount_path` is required** and must be absolute. Parent directories are created automatically. Agent working directory defaults to `/workspace`. Files are mounted read-only — the agent writes modified versions to new paths.

### Session outputs (output — agent → host)

The agent can write files to `/mnt/session/outputs/` during a session. These are automatically captured by the Files API and can be listed and downloaded afterwards:

```ts
// After the turn completes, list output files scoped to this session:
for await (const f of client.beta.files.list({
  scope_id: session.id,
  betas: ["managed-agents-2026-04-01"],
})) {
  console.log(f.filename, f.size_bytes);
  const resp = await client.beta.files.download(f.id);
  const text = await resp.text();
}
```

**Requirements:**
- The `write` tool (or `bash`) must be enabled for the agent to create output files.
- Session-scoped `files.list` / `files.download` captures outputs written to `/mnt/session/outputs/`.
- The filter parameter is **`scope_id`** (REST query param `?scope_id=<session_id>`). The SDK's files resource auto-adds only the `files-api-2025-04-14` header, so pass `betas: ["managed-agents-2026-04-01"]` explicitly (or both headers on raw HTTP) — without it the API may reject `scope_id` as an unknown field. Requires `@anthropic-ai/sdk` ≥ 0.88.0 / `anthropic` (Python) ≥ 0.92.0 — older versions don't type `scope_id`. The `ant` CLI does **not** expose this flag yet; use the SDK or curl.
- Pass the session ID returned by `sessions.create()` verbatim (e.g. `sesn_011CZx...`) — the API validates the prefix.
- There's a brief indexing lag (~1–3s) between `session.status_idle` and output files appearing in `files.list`. Retry once or twice if empty.

> **Fallback when `scope_id` filtering is unavailable** (older SDK, or endpoint returns an error): send a follow-up `user.message` asking the agent to `read` each file under `/mnt/session/outputs/` and return the contents. The agent streams the file bodies back as `agent.message` text. This works for text files only and costs output tokens — use it to unblock, not as the primary path.

This gives you a bidirectional file bridge: upload reference data in, download agent artifacts out.

### GitHub Repositories

Clones a GitHub repository into the session container during initialization, before the agent begins execution. The agent can read, edit, commit, and push via `bash` (`git`). Multiple repositories per session are supported — add one `resources` entry per repo. Repositories are cached, so future sessions that use the same repository start faster.

Repositories are attached for the lifetime of the session — to change which repositories are mounted, create a new session. You **can** rotate a repository's `authorization_token` on a running session via `client.beta.sessions.resources.update(resource_id, {session_id, authorization_token})`; the resource `id` is returned at session creation and by `resources.list()`.

**Fields:**

| Field | Required | Notes |
|---|---|---|
| `type` | ✅ | `"github_repository"` |
| `url` | ✅ | The GitHub repository URL |
| `authorization_token` | ✅ | GitHub Personal Access Token with repository access. **Never echoed in API responses.** |
| `mount_path` | ❌ | Path where the repository will be cloned. Defaults to `/workspace/<repo-name>`. |
| `checkout` | ❌ | `{type: "branch", name: "..."}` or `{type: "commit", sha: "..."}`. Defaults to the repo's default branch. |

**Token permission levels** (fine-grained PATs):
- `Contents: Read` — clone only
- `Contents: Read and write` — push changes and create pull requests

**How auth works:** `authorization_token` is never placed inside the container. `git pull` / `git push` and GitHub REST calls against the attached repository are routed through an Anthropic-side git proxy that injects the token after the request leaves the isolated environment. Code running in the container — including anything the agent writes — cannot read or exfiltrate it.

> ‼️ **To generate pull requests** you also need GitHub **MCP server** access — the `github_repository` resource gives filesystem + git access only. See `shared/managed-agents-tools.md` → MCP Servers. The PR workflow is: edit files in the mounted repo → push branch via `bash` (authenticated via the git proxy using `authorization_token`) → create PR via the MCP `create_pull_request` tool (authenticated via the vault).

**TypeScript:**

```ts
// 1. Create the agent — declare GitHub MCP (no auth here)
const agent = await client.beta.agents.create(
  {
    name: 'GitHub Agent',
    model: 'claude-opus-4-7',
    mcp_servers: [
      { type: 'url', name: 'github', url: 'https://api.githubcopilot.com/mcp/' },
    ],
    tools: [
      { type: 'agent_toolset_20260401', default_config: { enabled: true } },
      { type: 'mcp_toolset', mcp_server_name: 'github' },
    ],
  },
);

// 2. Start a session — attach vault for MCP auth + mount the repo
const session = await client.beta.sessions.create({
  agent: agent.id,
  environment_id: envId,
  vault_ids: [vaultId],  // vault contains the GitHub MCP OAuth credential
  resources: [
    {
      type: 'github_repository',
      url: 'https://github.com/owner/repo',
      authorization_token: process.env.GITHUB_TOKEN,  // repo clone token (≠ MCP auth)
      checkout: { type: 'branch', name: 'main' },
    },
  ],
});
```

**Python:**

```python
import os

agent = client.beta.agents.create(
    name="GitHub Agent",
    model="claude-opus-4-7",
    mcp_servers=[{
        "type": "url",
        "name": "github",
        "url": "https://api.githubcopilot.com/mcp/",
    }],
    tools=[
        {"type": "agent_toolset_20260401", "default_config": {"enabled": True}},
        {"type": "mcp_toolset", "mcp_server_name": "github"},
    ],
)

session = client.beta.sessions.create(
    agent=agent.id,
    environment_id=env_id,
    vault_ids=[vault_id],  # vault contains the GitHub MCP OAuth credential
    resources=[{
        "type": "github_repository",
        "url": "https://github.com/owner/repo",
        "authorization_token": os.environ["GITHUB_TOKEN"],  # repo clone token (≠ MCP auth)
        "checkout": {"type": "branch", "name": "main"},
    }],
)
```

---

## Files API

Upload and manage files for use as session resources, and download files the agent wrote to `/mnt/session/outputs/`.

| Operation        | Method   | Path                                  | SDK |
| ---------------- | -------- | ------------------------------------- | --- |
| Upload           | `POST`   | `/v1/files`                           | `client.beta.files.upload({ file })` |
| List             | `GET`    | `/v1/files?scope_id=...`              | `client.beta.files.list({ scope_id, betas: ["managed-agents-2026-04-01"] })` |
| Get Metadata     | `GET`    | `/v1/files/{id}`                      | `client.beta.files.retrieveMetadata(id)` |
| Download         | `GET`    | `/v1/files/{id}/content`              | `client.beta.files.download(id)` → `Response` |
| Delete           | `DELETE` | `/v1/files/{id}`                      | `client.beta.files.delete(id)` |

The `scope_id` filter on List scopes the results to files written to `/mnt/session/outputs/` by that session. Without the filter, you get all files uploaded to your account.
# Managed Agents — Events & Steering

## Events

### Sending Events

Send events to a session via `POST /v1/sessions/{id}/events`.

| Event Type                | When to Send                                        |
| ------------------------- | --------------------------------------------------- |
| `user.message`            | Send a user message |
| `user.interrupt`          | Interrupt the agent while it's running |
| `user.tool_confirmation`  | Approve/deny a tool call (when `always_ask` policy) |
| `user.custom_tool_result` | Provide result for a custom tool call |

### Receiving Events

Two methods:

1. **Streaming (SSE)**: `GET /v1/sessions/{id}/events/stream` — real-time Server-Sent Events. **Long-lived** — the server sends periodic heartbeats to keep the connection alive.
2. **Polling**: `GET /v1/sessions/{id}/events` — paginated event list (query params: `limit` default 1000, `page`). **Returns immediately** — this is a plain paginated GET, not a long-poll.

All received events carry `id`, `type`, and `processed_at` (ISO 8601; `null` if not yet processed by the agent).

> ⚠️ **Robust polling (raw HTTP).** If you bypass the SDK and roll your own poll loop, don't rely on `requests` or `httpx` timeouts as wall-clock caps — they're **per-chunk** read timeouts, reset every time a byte arrives. A trickling response (heartbeats, a wedged chunked-encoding body, a misbehaving proxy) can keep the call blocked indefinitely even with `timeout=(5, 60)` or `httpx.Timeout(120)`. Neither library has a "total wall-clock" timeout built in. For a hard deadline: track `time.monotonic()` at the loop level and break/cancel if a single request exceeds your budget (e.g. via a watchdog thread, or `asyncio.wait_for()` around async httpx). **Prefer the SDK** — `client.beta.sessions.events.stream()` and `client.beta.sessions.events.list()` handle timeout + retry sanely.
>
> If `GET /v1/sessions/{id}/events` (paginated) ever hangs after headers, you've likely hit `GET /v1/sessions/{id}/events` by mistake or a server-side stall — report it; don't treat it as a client-config problem.

### Event Types (Received)

Event types use dot notation, grouped by namespace:

| Event Type | Description |
| --- | --- |
| `agent.message` | Agent text output |
| `agent.thinking` | Extended thinking blocks |
| `agent.tool_use` | Agent used a built-in tool (`agent_toolset_20260401`) |
| `agent.tool_result` | Result from a built-in tool |
| `agent.mcp_tool_use` | Agent used an MCP tool |
| `agent.mcp_tool_result` | Result from an MCP tool |
| `agent.custom_tool_use` | Agent invoked a custom tool — session goes idle, you respond with `user.custom_tool_result` |
| `agent.thread_context_compacted` | Conversation context was compacted |
| `session.status_idle` | Agent has finished the current task, and is awaiting input. It's either waiting for input to continue working via a `user.message` or blocked awaiting a `user.custom_tool_result` or `user.tool_confirmation`. The `stop_reason` attached contains more information about why the Agent has stopped working. |
| `session.status_running` | Session has starting running, and the Agent is actively doing work. |
| `session.status_rescheduled` | Session is (re)scheduling after a retryable error has occurred, ready to be picked up by the orchestration system. |
| `session.status_terminated` | Session has terminated, entering an irreversible and unusable state.  |
| `session.error` | Error occurred during processing |
| `span.model_request_start` | Model inference started |
| `span.model_request_end` | Model inference completed |

The stream also echoes back user-sent events (`user.message`, `user.interrupt`, `user.tool_confirmation`, `user.custom_tool_result`).

---

## Steering Patterns

Practical patterns for driving a session via the events surface.

### Stream-first ordering

**Open the stream before sending events.** The stream only delivers events that occur *after* it's opened — it does not replay current state or historical events. If you send a message first and open the stream second, early events (including fast status transitions) arrive buffered in a single batch and you lose the ability to react to them in real time.

```ts
// ✅ Correct — stream and send concurrently
const [response] = await Promise.all([
  streamEvents(sessionId),   // opens SSE connection
  sendMessage(sessionId, text),
]);

// ❌ Wrong — events before stream opens arrive as a single buffered batch
await sendMessage(sessionId, text);
const response = await streamEvents(sessionId);
```

**For full history,** use `GET /v1/sessions/{id}/events` (paginated list) — the stream only gives you live events from connection onward.

### Reconnecting after a dropped stream

**The SSE stream has no replay.** If your connection drops (httpx read timeout, network blip) and you reconnect, you only get events emitted *after* reconnection. Any events emitted during the gap are lost from the stream.

**The consolidation pattern:** on every (re)connect, overlap the stream with a history fetch and dedupe by event ID:

```python
def connect_with_consolidation(client, session_id):
    # 1. Open the SSE stream first
    stream = client.beta.sessions.events.stream(session_id=session_id)

    # 2. Fetch history to cover any gap
    history = client.beta.sessions.events.list(
        session_id=session_id,
    )

    # 3. Yield history first, then stream — dedupe by event.id
    seen = set()
    for ev in history.data:
        seen.add(ev.id)
        yield ev
    for ev in stream:
        if ev.id not in seen:
            seen.add(ev.id)
            yield ev
```

### Message queuing

**You don't have to wait for a response before sending the next message.** User events are queued server-side and processed in order. This is useful for chat bridges where the user sends rapid follow-ups:

```ts
// All three go into one session; agent processes them in order
await sendMessage(sessionId, "Summarize the README");
await sendMessage(sessionId, "Actually also check the CONTRIBUTING guide");
await sendMessage(sessionId, "And compare the two");
// Stream once — agent responds to all three as a coherent turn
```

Events can be sent up to the Session at any time. There is no need to wait on a specific session status to enqueue new events via `client.beta.sessions.events.send()`

### Interrupt

An `interrupt` event **jumps the queue** (ahead of any pending user messages) and forces the session into `idle`. Use this for "stop" / "nevermind" / "cancel" commands:

```ts
await client.beta.sessions.events.send(sessionId, {
  events: [{ type: 'interrupt' }],
});
```

The agent stops mid-task. It does not see the interrupt as a message — it just halts. Send a follow-up `user` event to explain what to do instead.

> **Note**: Interrupt events may have empty IDs in the current implementation. When troubleshooting, use the `processed_at` timestamp along with surrounding event IDs.

### Event payloads

some events carry useful metadata beyond the status change itself:

`session.status_idle` — includes a `stop_reason` field which elaborates on why the session stopped and what type of further action is required by the user.
```json
{
  "id": "sevt_456",
  "processed_at": "2026-04-07T04:27:43.197Z",
  "stop_reason": {
    "event_ids": [
      "sevt_123"
    ],
    "type": "requires_action"
  },
  "type": "status_idle"
}
```

`span.model_request_end` contains a `model_usage` field for cost tracking and efficiency analysis:

```json
{
  "type": "span.model_request_end",
  "id": "sevt_456",
  "is_error": false,
  "model_request_start_id": "sevt_123",
  "model_usage": {
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 6656,
    "input_tokens": 3571,
    "output_tokens": 727
  },
  "processed_at": "2026-04-07T04:11:32.189Z"
}
```

**`agent.thread_context_compacted`** — emitted when the conversation history was summarized to fit context. Includes `pre_compaction_tokens` so you know how much was squeezed:

```json
{
  "id": "sevt_abc123",
  "processed_at": "2026-03-24T14:05:15.787Z",
  "type": "agent.thread_context_compacted"
}
```

### Archive

When done with a session, archive it to free resources:

```ts
await client.beta.sessions.archive(sessionId);
```

> Archiving a **session** is routine cleanup — sessions are per-run and disposable. **Do not generalize this to agents or environments**: those are persistent, reusable resources, and archiving them is permanent (no unarchive; new sessions cannot reference them). See `shared/managed-agents-overview.md` → Common Pitfalls.


# Managed Agents — Onboarding Flow

> **Invoked via `/claude-api managed-agents-onboard`?** You're in the right place. Run the interview below — don't summarize it back to the user, ask the questions.

Use this when a user wants to set up a Managed Agent from scratch. Three steps: **branch on know-vs-explore → configure the template → set up the session**. End by emitting working code.

> Read `shared/managed-agents-core.md` alongside this — it has full detail for each knob. This doc is the interview script, not the reference.

---

Claude Managed Agents is a hosted agent: Anthropic runs the agent loop on its orchestration layer and provisions a isolated environmented container per session where the agent's tools execute. You supply the agent config and the environment config; the harness — event stream, isolated environment orchestration, prompt caching, context compaction, and extended thinking — is handled for you.

**What you supply:**
- **An agent config** — tools, skills, model, system prompt. Reusable and versioned.
- **An environment config** — the isolated environment your agent's tools execute in (networking, packages). Reusable across agents.

Each run of the agent is a **session**.

---

## 1. Know or explore?

Ask the user:

> Do you already know the agent you want to build, or would you like to explore some common patterns first?

### Explore path — show the patterns

Four shapes, same runtime code path (`sessions.create()` → `sessions.events.send()` → stream). Only the trigger and sink differ.

| Pattern | Trigger | Example |
|---|---|---|
| Event-triggered | Webhook | GitHub PR push → CMA (GitHub tool) → Slack | # <------ MC maybe delete?
| Scheduled | Cron | Daily brief: browser + GitHub + Jira → CMA → Slack | # <------ MC maybe delete?
| Fire-and-forget PR | Human | Slack slash-command → CMA (GitHub tool) → PR passing CI |
| Research + dashboard | Human | Topic → CMA (web search + `frontend-design` skill) → HTML dashboard |

Ask which shape fits, then continue with the Know path using it as the reference.

### Know path — configure template

Three rounds. Batch the questions in each round; don't ask them one at a time.

**Round A — Tools.** Start here; it's the most concrete part. Three types; ask which the user wants (any combination):

| Type | What it is | How to guide |
|---|---|---|
| **Prebuilt Claude Agent tools** (`agent_toolset_20260401`) | Ready-to-use: `bash`, `read`, `write`, `edit`, `glob`, `grep`, `web_fetch`, `web_search`. Enable all at once, or individually via `enabled: true/false`. | Recommend enabling the full toolset. List the 8 tools so the user knows what they're getting. Full detail: `shared/managed-agents-tools.md` → Agent Toolset. |
| **MCP tools** | Third-party integrations (GitHub, Linear, Asana, etc.) via `mcp_toolset`. Credentials live in a vault, not inline. | Ask which services. For each, walk through MCP server URL + vault credentials. Full detail: `shared/managed-agents-tools.md` → MCP Servers + Vaults. |
| **Custom tools** | The user's own app handles these tool calls — agent fires `agent.custom_tool_use`, the app sends a result message back. | Ask for each tool: name, description, input schema. The app code that handles the event is *their* code — don't generate it. Full detail: `shared/managed-agents-tools.md` → Custom Tools. |

**Round B — Skills, files, and repos.** What the agent has on hand when it starts.

*Skills* — two types; both work the same way — Claude auto-uses them when relevant. Max 64 per agent.
- [ ] **Pre-built Agent Skills**: `xlsx`, `docx`, `pptx`, `pdf`. Reference by name.
- [ ] **Custom Skills**: skills uploaded to the user's org via the Skills API. Reference by `skill_id` + optional `version`. If the skill doesn't exist yet, walk the user through `POST /v1/skills` + `POST /v1/skills/{id}/versions` (beta header `skills-2025-10-02`). Full detail: `shared/managed-agents-tools.md` → Skills + Skills API.

*GitHub repositories* — any repos the agent needs on-disk? For each:
- [ ] Repo URL (`https://github.com/org/repo`)
- [ ] `authorization_token` (PAT or GitHub App token scoped to the repo)
- [ ] Optional `mount_path` (defaults to `/workspace/<repo-name>`) and `checkout` (branch or SHA)

Emit as `resources: [{type: "github_repository", url, authorization_token, ...}]`. Full detail: `shared/managed-agents-environments.md` → GitHub Repositories.

> ‼️ **PR creation needs the GitHub MCP server too.** `github_repository` gives filesystem access only — to open PRs, also attach the GitHub MCP server in Round A and credential it via a vault. The workflow is: edit files in the mounted repo → push branch via `bash` → create PR via the MCP `create_pull_request` tool.

*Files* — any local files to seed the session with? For each:
- [ ] Upload via the Files API → persist `file_id`
- [ ] Choose a `mount_path` — absolute, e.g. `/workspace/data.csv` (parents auto-created; files mount read-only)

Emit as `resources: [{type: "file", file_id, mount_path}]`. Max 999 file resources. Agent working directory defaults to `/workspace`. Full detail: `shared/managed-agents-environments.md` → Files API.

**Round C — Environment + identity:**
- [ ] Networking: unrestricted internet from the container, or lock egress to specific hosts? (If locked, MCP server domains must be in `allowed_hosts` or tools silently fail.)
- [ ] Name?
- [ ] Job (one or two sentences — becomes the system prompt)?
- [ ] Model? (default `claude-opus-4-7`)

---

## 2. Set up the session

Per-run. Points at the agent + environment, attaches credentials, kicks off.

**Vault credentials** (if the agent declared MCP servers):
- [ ] Existing vault, or create one? (`client.beta.vaults.create()` + `vaults.credentials.create()`)

Credentials are write-only, matched to MCP servers by URL, auto-refreshed. See `shared/managed-agents-tools.md` → Vaults.

**Kickoff:**
- [ ] First message to the agent?

Session creation blocks until all resources mount. Open the event stream before sending the kickoff. Stream is SSE; break on `session.status_terminated`, or on `session.status_idle` with a terminal `stop_reason` — i.e. anything except `requires_action`, which fires transiently while the session waits on a tool confirmation or custom-tool result (see `shared/managed-agents-client-patterns.md` Pattern 5). Usage lands on `span.model_request_end`. Agent-written artifacts end up in `/mnt/session/outputs/` — download via `files.list({scope_id: session.id, betas: ["managed-agents-2026-04-01"]})`.

---

## 3. Emit the code

Go straight from the last interview answer to the code — no preamble about the setup-vs-runtime split, no "the critical thing to internalize…", no lecture about `agents.create()` being one-time. The two-block structure below already shows that; don't narrate it. Generate **two clearly-separated blocks** per language detected (Python/TS/cURL — see SKILL.md → Language Detection):

**Block 1 — Setup (run once, store the IDs):**
1. `environments.create()` → persist `env_id`
2. `agents.create()` with everything from §Round A–C → persist `agent_id` and `agent_version`

Label: `# ONE-TIME SETUP — run once, save the IDs to config/.env`

**Block 2 — Runtime (run on every invocation):**
1. Load `env_id` + `agent_id` from config/env
2. `sessions.create(agent=AGENT_ID, environment_id=ENV_ID, resources=[...], vault_ids=[...])`
3. Open stream, `events.send()` the kickoff, loop until `session.status_terminated` or `session.status_idle && stop_reason.type !== 'requires_action'` (see `shared/managed-agents-client-patterns.md` Pattern 5 for the full gate — do not break on bare `session.status_idle`)

> ⚠️ **Never emit `agents.create()` and `sessions.create()` in the same unguarded block.** That teaches the user to create a new agent on every run — the #1 anti-pattern. If they need a single script, wrap agent creation in `if not os.getenv("AGENT_ID"):`.

Pull exact syntax from `python/managed-agents/README.md`, `typescript/managed-agents/README.md`, or `curl/managed-agents.md`. Don't invent field names.
# Managed Agents — Tools & Skills

## Tools

### Server tools vs client tools

| Type | Who runs it | How it works |
|---|---|---|
| **Prebuilt Claude Agent tools** (`agent_toolset_20260401`) | Anthropic, on the session's container | File ops, bash, web search, etc. Enable all at once or configure individually with `enabled: true/false`. |
| **MCP tools** (`mcp_toolset`) | Anthropic, on the session's container | Capabilities exposed by connected MCP servers. Grant access per-server via the toolset. |
| **Custom tools** | **You** — your application handles the call and returns results | Agent emits a `agent.custom_tool_use` event, session goes `idle`, you send back a `user.custom_tool_result` event. |

**Recommendation:** Enable all prebuilt tools via `agent_toolset_20260401`, then disable individually as needed.

**Versioning:** The toolset is a versioned, static resource. When underlying tools change, a new toolset version is created (hence `_20260401`) so you always know exactly what you're getting.

### Agent Toolset

The `agent_toolset_20260401` provides these built-in tools:

| Tool                   | Description                              |
| ---------------------- | ---------------------------------------- |
| `bash` | Execute bash commands in a shell session |
| `read` | Read a file from the local filesystem, including text, images, PDFs, and Jupyter notebooks |
| `write` | Write a file to the local filesystem |
| `edit` | Perform string replacement in a file |
| `glob` | Fast file pattern matching using glob patterns |
| `grep` | Text search using regex patterns |
| `web_fetch` | Fetch content from a URL |
| `web_search` | Search the web for information |

Enable the full toolset:

```json
{
  "tools": [
    { "type": "agent_toolset_20260401" }
  ]
}
```

### Per-Tool Configuration

Override defaults for individual tools. This example enables everything except bash:

```json
{
  "tools": [
    {
      "type": "agent_toolset_20260401",
      "default_config": { "enabled": true },
      "configs": [
        { "name": "bash", "enabled": false }
      ]
    }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `type` | ✅ | `"agent_toolset_20260401"` |
| `default_config` | ❌ | Applied to all tools. `{ "enabled": bool, "permission_policy": {...} }` |
| `configs` | ❌ | Per-tool overrides: `[{ "name": "...", "enabled": bool, "permission_policy": {...} }]` |

### Permission Policies

Control when server-executed tools (agent toolset + MCP) run automatically vs wait for approval. Does not apply to custom tools.

| Policy | Behavior |
|---|---|
| `always_allow` | Tool executes automatically (default) |
| `always_ask` | Session emits `session.status_idle` and pauses until you send a `tool_confirmation` event |

```json
{
  "type": "agent_toolset_20260401",
  "default_config": {
    "enabled": true,
    "permission_policy": { "type": "always_allow" }
  },
  "configs": [
    { "name": "bash", "permission_policy": { "type": "always_ask" } }
  ]
}
```

**Responding to `always_ask`:** Send a `user.tool_confirmation` event with `tool_use_id` from the triggering `agent_tool_use`/`mcp_tool_use` event:

```json
{ "type": "tool_confirmation", "tool_use_id": "sevt_abc123", "result": "allow" }
{ "type": "tool_confirmation", "tool_use_id": "sevt_def456", "result": "deny", "message": "Read .env.example instead" }
```

The optional `message` on a deny is delivered to the agent so it can adjust its approach.

To enable only specific tools, flip the default off and opt-in per tool:

```json
{
  "tools": [
    {
      "type": "agent_toolset_20260401",
      "default_config": { "enabled": false },
      "configs": [
        { "name": "bash", "enabled": true },
        { "name": "read", "enabled": true }
      ]
    }
  ]
}
```

### Custom Tools (Client-Side)

Custom tools are executed by **your application**, not Anthropic. The flow:

1. Agent decides to use the tool → session emits a `agent.custom_tool_use` event with inputs
2. Session goes `idle` waiting for you
3. Your application executes the tool
4. You send back a `user.custom_tool_result` event with the output
5. Session resumes `running`

No permission policy needed — you're the one executing.

```json
{
  "tools": [
    {
      "type": "custom",
      "name": "get_weather",
      "description": "Fetch current weather for a city.",
      "input_schema": {
        "type": "object",
        "properties": {
          "city": { "type": "string", "description": "City name" }
        },
        "required": ["city"]
      }
    }
  ]
}
```

### MCP Servers

MCP (Model Context Protocol) servers expose standardized third-party capabilities (e.g. Asana, GitHub, Linear). **Configuration is split across agent and vault:**

1. **Agent creation** declares which servers to connect to (`type`, `name`, `url` — no auth). The agent's `mcp_servers` array has no auth field.
2. **Vault** stores the OAuth credentials. Attach via `vault_ids` on session create.

This keeps secrets out of reusable agent definitions. Each vault credential is tied to one MCP server URL; Anthropic matches credentials to servers by URL.

**Agent side — declare servers (no auth):**

| Field | Required | Description |
|---|---|---|
| `type` | ✅ | `"url"` |
| `name` | ✅ | Unique name — referenced by `mcp_toolset.mcp_server_name` |
| `url` | ✅ | The MCP server's endpoint URL (Streamable HTTP transport) |

```json
{
  "mcp_servers": [
    { "type": "url", "name": "linear", "url": "https://mcp.linear.app/mcp" }
  ],
  "tools": [
    { "type": "mcp_toolset", "mcp_server_name": "linear" }
  ]
}
```

**Session side — attach vault:**

```json
{
  "agent": "agent_abc123",
  "environment_id": "env_abc123",
  "vault_ids": ["vlt_abc123"]
}
```

> 💡 **Per-tool enablement (empirical):** `mcp_toolset` has been observed accepting `default_config: {enabled: false}` + `configs: [{name, enabled: true}]` for an allowlist pattern. The API ref shows only the minimal `{type, mcp_server_name}` form.

> ⚠️ **MCP auth tokens ≠ REST API tokens.** Hosted MCP servers (`mcp.notion.com`, `mcp.linear.app`, etc.) typically require **OAuth bearer tokens**, not the service's native API keys. A Notion `ntn_` integration token authenticates against Notion's REST API but will **not** work as a vault credential for the Notion MCP server. These are different auth systems.

### Vaults — the MCP credential store

**Vaults** store OAuth credentials (access token + refresh token) that Anthropic auto-refreshes on your behalf via standard OAuth 2.0 `refresh_token` grant. This is the only way to authenticate MCP servers in the launch SDK.

#### Credentials and the isolated environment

Vaults store credentials; those credentials **never enter the isolated environment**. This is a deliberate security boundary — code running in the isolated environment (including anything the agent writes) cannot read or exfiltrate a vaulted credential, even under prompt injection. Instead, credentials are injected by Anthropic-side proxies **after** a request leaves the isolated environment:

- **MCP tool calls** are routed through an Anthropic-side proxy that fetches the credential from the vault and adds it to the outbound request.
- **Git operations on attached GitHub repositories** (`git pull`, `git push`, GitHub REST calls) are routed through a git proxy that injects the `github_repository` resource's `authorization_token` the same way.

**Not yet supported:** running other authenticated CLIs (e.g. `aws`, `gcloud`, `stripe`) directly inside the isolated environment. There is currently no way to set container environment variables or expose vault credentials to arbitrary processes. If you need one of these today:

- **Prefer an MCP server** for that service if one exists — it gets the same vault-backed injection.
- **Otherwise, register a custom tool:** the agent emits `agent.custom_tool_use`, your orchestrator (which already holds the credential) executes the call and returns `user.custom_tool_result` over the same authenticated event stream. No public endpoint is exposed; the isolated environment never sees the secret. See `shared/managed-agents-client-patterns.md` → Pattern 9.

**Do not put API keys in the system prompt or user messages as a workaround** — they persist in the session's event history.

> Formerly known internally as TATs (Tool/Tenant Access Tokens).

**Flow:**

1. Create a vault (`client.beta.vaults.create(...)`) — one per tenant/user, or one shared, depending on your model
2. Add MCP credentials to it (`client.beta.vaults.credentials.create(...)`) — each credential is tied to one MCP server URL
3. Reference the vault on session create via `vault_ids: ["vlt_..."]`
4. Anthropic auto-refreshes tokens before they expire; the agent uses the current access token when calling MCP tools

**Credential shape**:

```json
{
  "display_name": "Notion (workspace-foo)",
  "auth": {
    "type": "mcp_oauth",
    "mcp_server_url": "https://mcp.notion.com/mcp",
    "access_token": "<current access token>",
    "expires_at": "2026-04-02T14:00:00Z",
    "refresh": {
      "refresh_token": "<refresh token>",
      "client_id": "<your OAuth client_id>",
      "token_endpoint": "https://api.notion.com/v1/oauth/token",
      "token_endpoint_auth": { "type": "none" }
    }
  }
}
```

The `refresh` block is what enables auto-refresh — `token_endpoint` is where Anthropic posts the `refresh_token` grant. `token_endpoint_auth` is a discriminated union:

| `type` | Shape | Use when |
|---|---|---|
| `"none"` | `{type: "none"}` | Public OAuth client (no secret) |
| `"client_secret_basic"` | `{type: "client_secret_basic", client_secret: "..."}` | Confidential client, secret via HTTP Basic auth |
| `"client_secret_post"` | `{type: "client_secret_post", client_secret: "..."}` | Confidential client, secret in request body |

Omit `refresh` entirely if you only have an access token with no refresh capability — it'll work until it expires, then the agent loses access.

> 💡 **Getting an OAuth token.** How you obtain the initial access and refresh tokens depends on the MCP server — consult its documentation. Once you have them, store them in a vault credential using the shape above; Anthropic auto-refreshes via the `refresh.token_endpoint` from there.

**Scoping:** Vaults are workspace-scoped. Anyone with developer+ role in the API workspace can create, read (metadata only — secrets are write-only), and attach vaults. `vault_ids` can be set at session **create** time but not via session update (the SDK docstring says "Not yet supported; requests setting this field are rejected").

---

## Skills

Skills are reusable, filesystem-based resources that provide your agent with domain-specific expertise: workflows, context, and best practices that transform general-purpose agents into specialists. Unlike prompts (conversation-level instructions for one-off tasks), skills load on-demand and eliminate the need to repeatedly provide the same guidance across multiple conversations.

Two types — both work the same way; the agent automatically uses them when relevant to the task at hand:

| Type | What it is |
|---|---|
| **Pre-built Anthropic skills** | Common document tasks (PowerPoint, Excel, Word, PDF). Reference by name (e.g. `xlsx`). |
| **Custom skills** | Skills you've created in your organization via the Skills API. Reference by `skill_id` + optional `version`. |

**Max 64 skills per agent.** Agent creation uses `managed-agents-2026-04-01`; the separate Skills API (for managing custom skill definitions) uses `skills-2025-10-02`.

### Enabling skills on a session

Skills are attached to the **agent** definition via `agents.create()`:

```ts
const agent = await client.beta.agents.create(
  {
    name: "Financial Agent",
    model: "claude-opus-4-7",
    system: "You are a financial analysis agent.",
    skills: [
      { type: "anthropic", skill_id: "xlsx" },
      { type: "custom", skill_id: "skill_abc123", version: "latest" },
    ],
  }
);
```

Python:

```python
agent = client.beta.agents.create(
    name="Financial Agent",
    model="claude-opus-4-7",
    system="You are a financial analysis agent.",
    skills=[
        {"type": "anthropic", "skill_id": "xlsx"},
        {"type": "custom", "skill_id": "skill_abc123", "version": "latest"},
    ]
)
```

**Skill reference fields:**

| Field | Anthropic skill | Custom skill |
|---|---|---|
| `type` | `"anthropic"` | `"custom"` |
| `skill_id` | Skill name (e.g. `"xlsx"`, `"docx"`, `"pptx"`, `"pdf"`) | Skill ID from Skills API (e.g. `"skill_abc123"`) |
| `version` | — | `"latest"` or a specific version number |

### Skills API

| Operation             | Method   | Path                                            |
| --------------------- | -------- | ----------------------------------------------- |
| Create Skill          | `POST`   | `/v1/skills`                                    |
| List Skills           | `GET`    | `/v1/skills`                                    |
| Get Skill             | `GET`    | `/v1/skills/{id}`                               |
| Delete Skill          | `DELETE` | `/v1/skills/{id}`                               |
| Create Version        | `POST`   | `/v1/skills/{id}/versions`                      |
| List Versions         | `GET`    | `/v1/skills/{id}/versions`                      |
| Get Version           | `GET`    | `/v1/skills/{id}/versions/{version}`            |
| Delete Version        | `DELETE` | `/v1/skills/{id}/versions/{version}`            |


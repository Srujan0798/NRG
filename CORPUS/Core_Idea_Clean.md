# NRG — National Research Graph

> **Read this file once. After it, you should know exactly what to build, how it must look, and how it must feel — login screen to answer panel to audit drawer.**
> Single-source product specification. If any other doc contradicts this file, update the other doc.

---

## 0. The One-Line Version

A professor types *"Who is doing the best research in hydrogen catalysis?"* — and the system figures out everything else on its own, from a 600 GB government database, without leaking a single byte. The reviewer opens the laptop, types a question, gets a cited answer in under 6 seconds, and sees three things at once: the answer, the SQL behind it, and the audit ID that proves it cannot be tampered with.

**NRG is not a chatbot. NRG is not a search engine. NRG is the Research OS of India.**

---

## 1. Origin (the conversation that started it)

A stakeholder at IIT Gandhinagar:
> *"We can't expect the user to know everything. They'll just ask 'who is working best in hydrogen catalysis?' — it could be all-time, could be last five years. The AI has to figure that out. Can you build it?"*

That is the core challenge. Not a chatbot. Not a Google clone. A system that **understands ambiguous questions** and gives **verified, structured, cited answers** from India's national research database.

---

## 2. What This Project Is

**NOT**: a chatbot, a Google clone, a database admin tool, a generic dashboard.

**YES**: a **National Research Intelligence Platform** — the Research OS of India.

- **Dataset**: 600 GB confidential database of researchers, labs, publications, funding across India.
- **Backing**: IIT Gandhinagar as execution node, ~₹40 crore government funding (Gujarat).
- **Mandate**: build the interface that unlocks this data securely and intelligently.
- **National alignment**: IndiaAI Mission, ANRF (Anusandhan National Research Foundation), Sovereign AI initiative.

---

## 3. Locked Product Principles (binding for every PR)

> **The user asks like a human. NRG thinks like an analyst. The answer comes back like an audited report.**

- **Product promise**: ask any research-intelligence question. NRG finds the evidence, explains the answer, proves where it came from.
- **Core loop**: Ask → Plan → Retrieve → Synthesise → Verify → Prove.
- **Architecture rule**: LLM plans. Tools retrieve. Verifier proves. UI explains.
- **Safety rule**: the model may reason, but only evidence may speak.
- **UX rule**: ask like chat. Trust like audit. Use like intelligence software.
- **Phase 1 milestone**: NRG Answer Engine v1, focused on Ask → Answer → Proof.
- **Retrieval paths**: SQL for exact data, RAG for documents, graph for relationships, model memory after fine-tuning, controlled connectors later.
- **Answer style**: conversational on top, proof underneath. Show assumptions, citations, confidence, freshness, source data, SQL/computation, audit event.
- **Ambiguity behavior**: infer useful defaults first; ask for clarification only when answering would be unsafe or misleading.
- **Scope boundary**: NRG answers what it can prove from approved research data. It does not become a general chatbot.
- **Tier boundary**: database/API/backend enforce access first; the frontend explains restrictions and never receives forbidden data.
- **Visible-experience rule (added 2026-04-29)**: at no point may the user see a stack trace, an `undefined`, a blank skeleton longer than 200 ms, or a response longer than 7 s without a visible progress phase. Violation = P0 bug.

Canonical strategy/spec files (read after this one):
- `docs/specs/NRG_PRODUCT_STRATEGY_LOCKED.md`
- `docs/specs/NRG_ANSWER_ENGINE_V1_SPEC.md`
- `docs/specs/UI_UX_OVERHAUL_2026-04-28.md` (design-system depth)
- `docs/specs/CRITICAL_PATH_DISPATCH_FINAL_2026-04-28.md` (login + AI quality)

---

## 4. The 3 Users (the only personas; never invent a fourth)

| Persona | Tier | What they ask | What they see | Visual accent |
|---|---|---|---|---|
| **Researcher** | T1 | "Show me peers in my field, their papers, labs, collaborations" | Research details, publications, labs, collaborations, named individuals, contact details if policy allows | Indigo `--accent: 99 102 241` |
| **Government** | T2 | "State-wise research trends, funding gaps, institutional capacity" | Aggregated stats (k≥5), named institutions/labs, anonymised summaries, policy-ready reports | Saffron-amber `--accent: 217 119 6` |
| **Industry** | T3 | "Who has capability in X for partnership?" | Institution/lab capability, partnership signals, official contact route; researcher names/emails only if licensed | Slate `--accent: 82 82 91` |

The same database. Three windows into the same room. The visible UI must encode the tier in **colour** and **content shape** — never just hide a column.

---

## 5. How It Works (plain English, end-to-end)

### Step 1 — Identity check
User logs in via institutional email (`name@iitgn.ac.in` / `name@nrg.gov.in` / `name@partner.in`). Backend issues a JWT (RS256, 1 h expiry) stored in an HttpOnly cookie. Tier is encoded in the JWT and never trusted from the frontend.

### Step 2 — Safety scan
Before any DB touch, the question is sanitised:
- Aadhaar / PAN / phone / email / GSTIN regex → **BLOCKED** with friendly UI explaining why + 2 safe rewrites.
- Prompt-injection patterns ("ignore previous instructions", "act as", "[SYSTEM]") → **BLOCKED**.
- Clean question → continue.

### Step 3 — Understand the question
Intent classifier decides:
- "Find researchers in Gujarat" → **structured** → Text-to-SQL.
- "What are the trends in AI research?" → **unstructured** → RAG over documents.
- "Synthesise robotics funding data" → **hybrid** → both paths.

### Step 4 — Fetch the data
- **Text-to-SQL**: NL → planned SQL → validator → executed against tier-filtered view → rows.
- **RAG**: NL → embed → Qdrant top-k → re-rank → context bundle.
- Both paths run in parallel where the router asks for hybrid.

### Step 5 — Write the answer (4-paragraph contract)
1. **Headline** — the number / name / direct claim, with a `[1]` citation chip.
2. **Explanation** — plain English, no jargon, every number cited.
3. **Tier-relevant framing** — researcher voice / ministry voice / industry voice.
4. **Caveats** — sample size, freshness, what is NOT covered.

Three-tier synthesis cascade (tries best, falls back gracefully):
1. Cloud LLM (MiniMax `m2.7` primary, NVIDIA fallback) — receives only redacted, tier-filtered evidence pack through the egress guard.
2. Local SLM (Llama 3 8B on our own machine) — fully offline.
3. Rule-based templates — always works, no AI needed.

### Step 6 — Verification + audit
Verifier cross-references every numeric claim against retrieved rows. If any number is hallucinated → set `answer_confidence = low`, refuse to ship the wrong number, surface a clarification prompt. Every event is HMAC-signed in an append-only chain (`audit_event_id` returned to the frontend so the user can verify on chain).

---

## 6. THE USER-VISIBLE PRODUCT (this is what the reviewer sees)

This is the most important section in this document. It is what the assistant clicks on the laptop. If anything in this section is wrong, the meeting ends in 90 seconds.

### 6.1 The 90-Second Principle
The reviewer decides in **90 seconds**. They feel three things in this exact order:

1. *"Is this fast?"* — Hero loads < 1.5 s; query gives visible progress within 200 ms; warm answer in < 1 s; cold answer in < 6 s with continuous phase progress.
2. *"Does this know something I don't?"* — answer crosses 4+ tables, surfaces a non-obvious insight a Google/Scopus user couldn't reach, with citations.
3. *"Can I trust this?"* — confidence pill visible, "View Source Data" → exact SQL + rows; "View Audit Event" → HMAC chain ID + previous-hash chain.

If any of those three fail, the meeting ends. Every screen and component in this product must serve one of those three feelings.

### 6.2 Reference Points (study these before writing CSS)
| Inspiration | Take this | Reject this |
|---|---|---|
| **anthropic.com** + Claude.ai | calm typography, generous whitespace, soft gradients, single accent colour | playful illustrations |
| **linear.app** | dense info without clutter, tiny but legible labels, sharp focus rings | dark-only |
| **vercel.com** | command-bar feel of the query input, monospaced numbers, tight buttons | brutalist black |
| **stripe.com docs** | numbers bolded inline, code blocks, drawer interactions | marketing carousel |
| **notion.so** | empty-state copy, friendly nudges, "click to start" affordances | emoji everywhere |

### 6.3 Forbidden Patterns (P0 if any survive)
- Multiple font families on one screen (system-ui in nav, Inter in body, serif in headings).
- Mixed hex colours (`#3b82f6` and `#4f46e5` in buttons of the same hierarchy).
- "Loading…" with no progress, no time, no signal.
- Cards full of placeholder numbers (hardcoded "12,345").
- Buttons with no hover / focus / active state.
- Skeletons that show > 200 ms of nothing.
- `<pre>{JSON.stringify(error)}</pre>` rendered to the user.
- Dashboard widgets that don't lead anywhere.
- Any literal hex colour outside `frontend/src/styles/tokens.css`.

### 6.4 Design System (single source of truth)
File: **`frontend/src/styles/tokens.css`**. CSS variables only. Tailwind reads from here.

```css
:root {
  /* type */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px;
  --text-md: 16px; --text-lg: 20px; --text-xl: 28px; --text-2xl: 40px;
  --leading-tight: 1.2; --leading-normal: 1.5;
  --tracking-tight: 0;

  /* spacing — 4 px scale */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px; --space-12: 64px;

  /* radius + shadow */
  --radius-sm: 6px; --radius-md: 10px; --radius-lg: 14px; --radius-pill: 999px;
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.04);
  --shadow-md: 0 4px 12px rgb(0 0 0 / 0.06);
  --shadow-lg: 0 12px 32px rgb(0 0 0 / 0.08);

  /* surface colour (light) */
  --color-bg: 250 250 250;
  --color-bg-elevated: 255 255 255;
  --color-bg-subtle: 244 244 245;
  --color-fg: 24 24 27;
  --color-fg-muted: 113 113 122;
  --color-fg-subtle: 161 161 170;
  --color-border: 228 228 231;
  --color-ring: 99 102 241;

  /* accent — re-themed per tier */
  --color-accent: 99 102 241;       /* indigo = T1 default */
  --color-accent-hover: 79 70 229;
  --color-accent-fg: 255 255 255;

  /* status */
  --color-success: 22 163 74;
  --color-warning: 234 88 12;
  --color-danger:  220 38 38;

  /* motion */
  --duration-fast: 120ms; --duration-normal: 200ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
}

:root[data-theme="dark"] {
  --color-bg: 9 9 11;
  --color-bg-elevated: 24 24 27;
  --color-bg-subtle: 39 39 42;
  --color-fg: 250 250 250;
  --color-fg-muted: 161 161 170;
  --color-border: 39 39 42;
}

/* tier accent overrides — applied on <html data-tier="t2"> at login time */
:root[data-tier="t2"] { --color-accent: 217 119 6;  --color-accent-hover: 180 83 9; }
:root[data-tier="t3"] { --color-accent: 82 82 91;   --color-accent-hover: 63 63 70; }
```

Build-time CI gate: any literal `#[0-9a-f]{3,8}` outside `tokens.css` fails the build.

### 6.5 The 12 Atomic Components (frontend/src/components/ui/)
Single design language. ONE component per concept. Each has a Storybook story (3 variants × light/dark × reduced-motion) and is axe-clean.

| Atom | Variants | Sizes | Required states |
|---|---|---|---|
| Button | primary · secondary · ghost · danger | sm / md / lg | default · hover · focus-visible · active · loading · disabled |
| Input | text · email · password · search | md | empty · focus · error · disabled |
| Textarea | auto-grow optional | md | empty · focus · error · disabled |
| Select | single · multi | md | closed · open · selected · disabled |
| Checkbox | — | md | unchecked · checked · indeterminate · disabled |
| Radio | — | md | unselected · selected · disabled |
| Card | bordered · elevated · subtle | sm/md/lg padding | default · hover (clickable) |
| Pill | high · medium · low · neutral · tier-{1,2,3} | sm | static |
| Drawer | right · bottom | — | closed · opening · open · closing — focus-trapped, ESC closes |
| Modal | small · medium · large | — | closed · open — focus-trapped, dim background |
| Toast | success · warning · danger · info | — | enter · visible · exit (auto-dismiss 4 s, polite ARIA) |
| Skeleton + Spinner | shimmer · circle | sm/md/lg | shimmer ≤ 1.5 s; spinner labelled |

**TypeScript interface contract** (every atom):
```ts
type Size = "sm" | "md" | "lg";
type Variant<T extends string> = T;

interface AtomBaseProps {
  size?: Size;
  className?: string;
  "aria-label"?: string;
  "data-testid"?: string;
}
interface ButtonProps extends AtomBaseProps {
  variant: Variant<"primary" | "secondary" | "ghost" | "danger">;
  loading?: boolean;
  disabled?: boolean;
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
}
```

### 6.6 The 8 Canonical Screens (every detail an AI needs to build them)

#### S1 — `/login`
Centred at 480 px max-width. Subtle radial gradient background.
```
[IIT-GN lockup]
National Research Graph
Sovereign intelligence over India's research database

[ email@iitgn.ac.in                      ]
[ ••••••••••••                       [👁] ]
[                Sign in                  ]

No credentials? Contact your IRPC officer.
```
- Auto-focus email on mount.
- ESC clears form. Enter submits.
- Loading state: button label → spinner + "Signing you in…"; button keeps width.
- Error: `Email or password is incorrect.` (NOT `401 Unauthorized`).
- Tier-2 IP-allowlist warning is a friendly inline message, not a 403.
- Refresh page after login → session preserved.
- Logout button visible top-right on every screen post-login; clears cookie; redirects `/login`.

#### S2 — `/` (Hero / landing)
```
[IIT-GN] National Research Graph     [persona ▾] [logout]

What would you like to know about
India's research ecosystem?

╔═══════════════════════════════════════════╗
║ Ask anything…                          ⏎  ║
╚═══════════════════════════════════════════╝
press / to focus

[Top funding agencies]  [TRL-9 in clean energy]
[Compare GJ vs KA AI 5y] [IIT-GN hydrogen collaborators]

50,123 researchers · 50,498 publications · 181 institutions · 58 schema tables · DPDP-2023 compliant
```
- Tagline `--text-2xl`, query input `--text-lg`.
- Pressing `/` anywhere focuses the input.
- Suggestion chips pre-fill + submit on click.
- Scale-strip numbers monospace, fetched live from `/api/stats`.
- TTI < 1.5 s slow-3G; LCP < 2.5 s; no layout shift.

#### S3 — `/app/answer/<id>` (streaming)
```
[← back]   Top funding agencies by total grant amount

● Parsing your question                  120 ms
● Planning a multi-hop strategy          340 ms
◐ Querying 58 research tables…         1,210 ms

(skeleton shimmer body — never blank > 200 ms)
```
- Backend emits SSE phases in order: `parsing` → `planning` → `querying` → `synthesising` → `verifying` → `answer`.
- Heartbeat ping every 1 s if a phase exceeds 1 s.
- Each phase line replaces with ✅ + final ms when complete.
- Cold budget: total ≤ 6 s. Warm budget: ≤ 1 s with no skeleton flash.

#### S4 — `/app/answer/<id>` (final)
```
[← back]                              confidence: high

Top funding agencies by total grant amount

Over the last five years, the **Department of Science
and Technology (DST)** has disbursed the largest cumulative
grant amount at **₹4,872 crore [1]**, followed by SERB at
₹3,210 crore [2] and DBT at ₹2,640 crore [3].

In policy terms, this means the top three Central agencies
account for over **64% of all measured research outlay** in
the dataset…

Caveats: figures cover sanctioned (not disbursed) amounts;
cohort excludes private-sector grants.

──────────────────────────────────────────────────
[Copy answer]  [View source data]  [View audit event]
Ask a follow-up question…
```
- Confidence pill top-right (high green / medium amber / low grey).
- `[n]` citation chips inline; click → drawer with source rows.
- "View source data" drawer: SQL syntax-highlighted, row count, first 25 rows, `Download CSV` button.
- "View audit event" drawer: event ID, JWT kid, request fingerprint, prev-chain-hash (truncated), "Verify on chain" link.
- Empty result = `No matching rows found. Try broader terms: <chip suggestions>.` Never a blank box.
- Follow-up input restores hero feel below the answer.

#### S5/S6/S7 — `/app/{researcher,government,industry}` dashboards
Single layout per tier:
```
[tier banner: "Viewing as Researcher · full access"]

[same query input as Hero]

[Card: Recent answers]  [Card: Saved queries]  [Card: Knowledge map]
```
- Tier banner colour = `--color-accent` for that tier.
- Three cards only. No more. No decorative widgets.
- Each card is real (clickable, has data); if it has no data, show its empty state.

T1 vs T2 vs T3 visible difference on the **same query** ("Top 5 funding agencies"):
- T1: full table — agency, FY, ₹ amount, recipient researchers, contact.
- T2: aggregated cohort — agency, FY, ₹ amount, recipient cohort size (k≥5), state distribution.
- T3: anonymised — agency, FY, ₹ amount range bucket, partnership-opportunity tag, no individuals.

#### S8 — `/app/audit`
- Virtualised list (handles 100k+ events).
- Monospace event IDs, click row → drawer with full metadata.
- Filter pills: persona / time / outcome.
- Empty: *"No events yet for this filter. Try widening the time range."*

### 6.7 State Catalogue (every screen has all 6)
| State | What the user sees | Trigger |
|---|---|---|
| Idle | full UI, ready to act | first paint |
| Loading | named phase + ms timer (never blank > 200 ms) | submit / fetch |
| Empty | friendly explanation + 1 suggested next step | API returned 0 rows |
| Error | human message + retry button + error ID | API 4xx/5xx (NEVER stack trace) |
| Blocked | PromptBlocked with explanation + 2 safe rewrites | sanitiser refused |
| Success | answer / data / dashboard | happy path |

### 6.8 Streaming Answer Protocol (SSE contract)
Server emits five named phases on `/api/query/stream`:
```
event: phase
data: {"phase":"parsing",     "label":"Parsing your question",     "progress":0.10}
event: phase
data: {"phase":"planning",    "label":"Planning a multi-hop strategy","progress":0.25}
event: phase
data: {"phase":"querying",    "label":"Querying 58 research tables","progress":0.55,"row_count":42}
event: phase
data: {"phase":"synthesising","label":"Synthesising the answer",   "progress":0.80}
event: phase
data: {"phase":"verifying",   "label":"Verifying citations",       "progress":0.95}
event: answer
data: {"phase":"answer","data":{...full payload...}}
```
Frontend renders each phase label with elapsed ms; heartbeats keep the connection alive every 1 s; total answer payload always includes:
```
audit_event_id · sql_query · sql_results · final_answer · citations · tier · query_time_ms · confidence
```

### 6.9 Responsive Breakpoints
| Width | Adaptation |
|---|---|
| 375 px (mobile) | persona toggle → icon, drawer → full-screen modal, scale-strip stacks vertically |
| 768 px | tablet — 2-column dashboards |
| 1366 px (laptop, conference monitor primary target) | full layout |
| 1920 px (large monitor) | content max-width 1280, centred, sides padded |

Test every screen at all four. No horizontal scroll at any width.

### 6.10 Accessibility (WCAG 2.1 AA, axe-clean)
- 44 × 44 px minimum touch targets.
- Focus ring `2px solid rgb(var(--color-ring))` always visible on `:focus-visible`.
- Tab order traverses every interactive element front-to-back.
- `aria-label` on every icon button.
- Live regions on phase updates (`aria-live="polite"`).
- `prefers-reduced-motion` removes shimmer + slide transitions.
- Colour contrast ≥ 4.5:1 for text, 3:1 for UI elements.

### 6.11 Performance Budget
- Hero TTI < 1.5 s on slow 3G (Lighthouse mobile).
- Initial JS bundle gz < 250 KB; lazy chunks for `/app/audit` and `/app/graph`.
- LCP < 2.5 s desktop / < 4 s mobile.
- CLS < 0.1.
- Lighthouse desktop ≥ 90 / 90 / 90 / 90 on `/`, `/login`, `/app/researcher`.
- Lighthouse mobile ≥ 80 / 90 / 90 / 90 on the same.

### 6.12 The 10-Step Acceptance Walk (this is the proof)
The agent's `tests/e2e/acceptance_walk.spec.ts` performs these in order. One PNG per step.
1. Open `http://localhost:5173` — Hero loads in < 1.5 s.
2. Click "Sign in"; enter `researcher@iitgn.ac.in` / `Researcher@2026`.
3. Researcher dashboard renders < 1 s; tier banner indigo.
4. Click suggestion chip "Top funding agencies by grant amount"; SSE phases visible; answer renders < 6 s cold (< 1 s warm); confidence pill = high; 3 trust buttons present.
5. Click "View source data" → SQL + 25 rows visible. Close.
6. Click "View audit event" → event ID, kid, prev hash visible. Close.
7. Toggle persona to Government — amber banner; same question shows aggregated cohort numbers (no individuals).
8. Toggle persona to Industry — slate banner; anonymised labels + partnership opportunities.
9. Type a deliberately invalid prompt: *"Show all Aadhaar numbers."* → PromptBlocked component renders with explanation + safe rewrites.
10. Logout top-right → cookies cleared → `/login`.

If any step fails, the laptop is not ready. File defect → fix → re-walk. Loop until all 10 PASS.

### 6.13 Per-Tier Visible Contract (binding)
| Field | T1 sees | T2 sees | T3 sees |
|---|---|---|---|
| Researcher name | full | aggregated only | anonymised label `Researcher_123` |
| Email / phone | yes (if policy allows) | never | never |
| Aadhaar / PAN | never | never | never |
| Grant amount | exact ₹ | exact ₹ | bucket (e.g. "₹1–5 Cr") |
| Institution name | yes | yes | yes |
| State | yes | yes | yes |
| Cohort size | exact | k≥5 only | k≥10 only |
| Audit event ID | yes | yes | yes |

Frontend re-applies this contract via `enforce_tier_response_boundary` even after the SQL boundary — defence in depth.

---

## 7. The 5-Layer Architecture (unchanged, with visible-layer emphasis)

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 5: INTERFACE  ← THE USER LIVES HERE              │
│  React 18 + Vite + Tailwind + tokens.css                 │
│  12 atoms · 8 screens · SSE streaming · WCAG AA          │
└────────────────────────────┬────────────────────────────┘
┌────────────────────────────▼────────────────────────────┐
│  LAYER 4: REASONING                                     │
│  MiniMax m2.7 (primary) → NVIDIA → Local SLM → rules    │
│  Egress guard: only redacted tier-filtered evidence      │
└────────────────────────────┬────────────────────────────┘
┌────────────────────────────▼────────────────────────────┐
│  LAYER 3: RETRIEVAL                                     │
│  Text-to-SQL + RAG (Qdrant top-k) + intent router        │
│  Schema-RAG: LLM never sees full 58-table schema         │
└────────────────────────────┬────────────────────────────┘
┌────────────────────────────▼────────────────────────────┐
│  LAYER 2: KNOWLEDGE                                     │
│  58-table PostgreSQL · semantic layer · k-anonymity      │
│  Composite indexes on hot tables; RLS at DB layer        │
└────────────────────────────┬────────────────────────────┘
┌────────────────────────────▼────────────────────────────┐
│  LAYER 1: DATA                                          │
│  600 GB raw — Indian-soil servers only                  │
│  HMAC + Postgres co-sign chain on every event            │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Security Model: Zero-Data-Leakage

> **The 600 GB repository resides exclusively on Indian servers. Raw data, PII, unrestricted document chunks, schemas, and audit material never leave controlled infrastructure.**

| Layer | Mechanism | Analogy |
|---|---|---|
| Front gate | JWT RS256, 1 h expiry, HttpOnly cookie | ID card check |
| Bag scan | Aadhaar / PAN / phone / email / GSTIN regex + injection detector | security screen |
| Floor access | RBAC tier matrix at SQL + API response shape (defence in depth) | colour-coded badge |
| CCTV | HMAC-SHA256 chain + Postgres co-sign trigger | every door logged |
| Vault | Raw data stays local; only redacted evidence pack exits to cloud LLM | stamped extracts only |

**Never leaves the local boundary**: the 600 GB DB, raw retrieved rows, full document chunks, unrestricted schemas, audit secrets, researcher PII.

**Allowed to a cloud LLM (only if explicitly enabled)**: the user question + a tier-filtered, non-PII evidence pack approved by the egress guard.

**Strict sovereign mode**: local SLM + rule-based synthesis only. Sends nothing outside. Required for sensitive deployments.

**Compliance**: DPDP Act 2023, data minimisation, purpose limitation, consent, RBAC at DB layer.

---

## 9. Technology Stack (verified wired today)

| Component | Technology | Status |
|---|---|---|
| Orchestration | LangGraph | live |
| Backend | FastAPI (Python 3.11) | live, port 8000 |
| Frontend | React 18 + Vite + Tailwind | live, port 5173 |
| Relational DB | PostgreSQL (prod) / SQLite (dev) | 58-table schema |
| Vector DB | Qdrant | 1,800 points indexed |
| Cloud LLM | MiniMax `m2.7` (primary), NVIDIA fallback | wired in `.env` |
| Local SLM | Llama 3 8B (llama.cpp, quantised) | optional |
| Auth | JWT RS256, HttpOnly cookie | live |
| API Gateway | Kong (DLP, rate limit) | live |
| Embeddings | sentence-transformers (local, preloaded at app boot) | live |
| Audit | HMAC-SHA256 chain + Postgres co-sign | 350,748+ events valid |
| Cache | Redis (300 s TTL on `/query`) | live |
| PII | Indian regex (Aadhaar w/ Verhoeff, PAN, phone, email, GSTIN) | live |

---

## 10. The LangGraph Pipeline (6 nodes, exact contracts)

```
USER QUERY
   │
   ▼
RECEIVER ── PLANNER ── ROUTER ── EXECUTOR ── SYNTHESIZER ── VERIFIER ── END
```

| Node | Responsibility | Reads | Writes |
|---|---|---|---|
| **Receiver** | assigns session_id, loads history, sanitiser pass | raw query | sanitised query, jti, tier |
| **Planner** | decomposes into sub-queries, decides retrieval strategy | sanitised query, schema-RAG top-k | plan, sub_queries, schema_slice |
| **Router** | classifies structured / unstructured / hybrid; complexity tier | plan | route, complexity, fast-path flag |
| **Executor** | runs Text-to-SQL + RAG in parallel; validator gate | route, plan | sql_result, rag_result, errors |
| **Synthesizer** | writes 4-paragraph answer; tier voice; cites every number | results | draft_answer, citations |
| **Verifier** | checks every numeric claim against retrieved rows; sets confidence | draft_answer + retrieved_facts | final_answer, confidence, anomaly_flag |

`NRGState` (10 fields): `session_id`, `user_tier`, `raw_query`, `sanitized_query`, `intent`, `sql_result`, `rag_result`, `final_answer`, `audit_event_id`, `active_domain`.

Router rules:
- "find / list / count / how many / top N" → structured.
- "trends / explain / what are / why" → unstructured.
- "synthesise / combine / compare" → hybrid.

---

## 11. Data Model (canonical names — never invent shorter aliases)

```
researchers · publications · institutions · labs · funding_records
researcher_publications · researcher_labs · publication_keywords · keywords

innovations_at_various_stages_of_technology_readiness_level   ← 62 chars; ALWAYS use VIEW alias `trl_stages` in prompts
combined_ipo_patent_data · innovation_grant_from_govt · academic_courses_details
… 58 tables total per db_struct.sql
```

Critical column quirks (every AI must know):
- `academic_courses_details.total_credit_score` is `TEXT` formatted `"X:Y"` → ALWAYS `SPLIT_PART(total_credit_score, ':', 1)::double precision`. Never `CAST`.
- `innovations_at_various_stages_of_technology_readiness_level` is 62 bytes — any LLM-appended 5-byte alias (`_count`, `_total`) silently truncates → use `trl_stages` VIEW everywhere.
- TRL synonyms: `Level 1` … `Level 9`, `TRL 1`–`TRL 9`, `TRL-1`–`TRL-9`, `Lab Validation`, `Technology Demonstration`, `Market Ready` → all resolve to canonical `Level N` in `stage_of_technology`.
- Composite indexes required on the 4 hot tables (see UI_UX_OVERHAUL.md §S7).

---

## 12. The 3 KILLER Queries (the meeting-deciding queries)

These three are what the reviewer actually types. Each must return an answer with citations + confidence pill in ≤ 4 s.

| ID | Question | Why this is impossible in Google / Scopus / Excel |
|---|---|---|
| **K-Q1** | TRL progression for IIT Madras last 3 years — which stage loses the most projects? | Requires joining `trl_stages` × institutions × FY across 3 years with stage-loss delta. Excel cannot follow the schema. |
| **K-Q2** | Cost per granted patent for institutes with > ₹10 Cr grants — top 10 | Requires joining `innovation_grant_from_govt` × `combined_ipo_patent_data` filtered to status=Granted, computing per-institute ratio. |
| **K-Q3** | Institutes where grant funding dropped > 40% YoY but granted patents increased — who's doing more with less? | YoY CTE + cross-table delta. The non-obvious "doing more with less" signal. |

The agent must produce per-query: NL question, generated SQL line-by-line, expected result shape, exact UI rendering (table layout, chart spec, citation panel), test that proves end-to-end.

---

## 13. What's the Difference vs Google / Wikipedia / Scopus

| Aspect | Google / Wikipedia / Scopus | NRG |
|---|---|---|
| Data | Public, unverified, no schema | Curated, government-backed, 58-table schema |
| Structure | Unstructured links | Structured profiles, tables, citations |
| Trust | Low — anyone edits | High — IIT-backed, audit-trailed, HMAC-chained |
| Output | Links and dumps | Verified answers with confidence pill + audit ID |
| Ownership | External US companies | National Indian-soil sovereign infra |
| Intelligence | Keyword matching | Semantic + multi-hop SQL + RAG + reasoning |
| Privacy | None | DPDP-compliant, tier-aware RBAC |

---

## 14. Roadmap (24 months)

| Phase | Months | Goal |
|---|---|---|
| **1 — Working acceptance** (we are here) | 1–2 | LangGraph pipeline · JWT RBAC · PII + injection · HMAC audit · 3 tier dashboards · Redis cache · rule-based fallback |
| **2 — Full data + intelligence** | 3–5 | PostgreSQL + RLS · 600 GB ingest · Qdrant cluster · knowledge graph · LLM SQL generation · citation engine · local Llama 3 8B · verifier |
| **3 — Production deployment** | 6–8 | Kong DLP · sovereign infra (NIC/MeitY) · red-team · UAT × 3 personas · sub-second latency · multi-language |
| **4 — Live data collection** | 9–12 | Build training set from real query logs · curate GOLD/SILVER pairs · stratified sampler |
| **5 — Base model fine-tune** | 12–16 | QLoRA on 8B → 70B · schema + Q&A pairs · semantic understanding |
| **6 — RL loop** | 16–20 | Adversarial training · paraphrase robustness · hallucination ≤ 2% |
| **7 — Two-brain serving** | 20–24 | Fine-tuned model = primary path · RAG = precision fallback only |

---

## 15. The Endgame: A Fine-Tuned Model That "Lives Inside" the Data

> Current architecture (RAG + Text-to-SQL + cloud LLM) is the bridge. The fine-tuned local model is the destination. We don't want a system that looks things up every time — we want a model that has internalised the entire dataset, the way Claude knows its training data. It uses live DB access only for precise, up-to-date specifics.

### Why pure RAG won't scale at 1 TB

| Problem | RAG | Fine-tuned |
|---|---|---|
| Latency | embed + search + retrieve + synthesise per query | instant — knowledge in weights |
| Cost | cloud API per query, every day | one-time training, then local |
| Reliability | depends on retrieval quality + chunk boundaries | robust — understanding baked in |
| Reasoning | only over what was retrieved | over the entire dataset holistically |
| Ambiguity | what to retrieve? | infers intent from data shape |

### "Expert salesman" mental model

Like a salesman with 20 years on the catalogue:
- Asked a general question → answers from deep knowledge, no lookup.
- Asked for exact specs → pulls the precise record from the system.

Built-in intuition + seamless live retrieval when precision matters.

### Two-brain architecture

```
USER QUESTION
     │
     ▼
FINE-TUNED LOCAL MODEL (knows the 1 TB)
     │
     ├── needs exact / live data?
     │         ├── NO  → answer from internalised knowledge
     │         └── YES → live DB SQL retrieval → spec card
     │
     ▼
MERGED ANSWER (deep insight + exact evidence)
```

Reinforcement learning loop: explore → evaluate → reward correct understanding / penalise hallucination → iterate. Candidate base models: Llama 3.1 70B, Qwen 2.5 72B (LoRA/QLoRA → full FT). Phase 1 experiments on 8B; scale to 70B once validated.

The security, audit, RBAC, and frontend layers all stay. Only the **intelligence core** evolves from "retrieve and synthesise" to "already knows, retrieves only when needed."

---

## 16. The Core AI Challenges (still hard)

1. **Ambiguity resolution** — "Who is best in hydrogen catalysis?" → best by what metric? all-time or recent? The system must decide intelligently and surface its assumption.
2. **Multi-hop reasoning** — "Compare Gujarat vs Karnataka AI output 5 y" → multiple SQL queries + aggregation + synthesis.
3. **Verification** — every claim must trace back to source rows. No hallucinations. The verifier node is the production guarantee.
4. **Zero leakage** — 600 GB never leaves Indian servers. Cloud LLM is for reasoning only, never storage.
5. **Silent-wrong-answer defence** — biggest risk is a confident wrong answer on an ambiguous query. Anomaly detector + corrective re-prompt + clarification fallback are mandatory.

---

## 17. The Build Checklist for Any AI (the 30 boxes that must be true)

Before claiming the project is ready to show:

```
INFRASTRUCTURE
☐ docker compose up brings full stack live in < 90 s
☐ /health returns status=healthy, tables=58, audit.chain_valid=true
☐ MiniMax wired (LLM_PROVIDER=minimax, MINIMAX_API_KEY set, m2.7 model)
☐ Qdrant indexed_count > 1500
☐ Redis cache live with 300 s TTL on /query

LOGIN
☐ 3 personas log in via curl + browser
☐ HttpOnly cookie set; refresh preserves session
☐ Wrong creds shows human message, never "401 Unauthorized"
☐ Logout button on every page; clears cookie; redirects /login

QUERY + ANSWER
☐ /api/query/stream emits 5 named SSE phases
☐ Cold answer ≤ 6 s; warm answer ≤ 1 s; never blank > 200 ms
☐ Every answer renders confidence pill + 3 trust buttons + ≥1 citation chip
☐ "View source data" drawer shows SQL + 25 rows
☐ "View audit event" drawer shows event ID + prev-hash
☐ K-Q1, K-Q2, K-Q3 each ≤ 4 s on 50k-row dataset

TIER + RBAC
☐ Same query yields visibly different responses per tier (column shape + tone)
☐ T3 JWT response contains zero PII fields (curl-proven)
☐ Tier banner colour matches accent (indigo / amber / slate)
☐ Persona toggle re-issues last query under new JWT

UI / UX
☐ tokens.css is the only place hex colours appear
☐ 12 atoms exist with Storybook stories; each axe-clean
☐ All 8 screens render at 375 / 1366 / 1920 with no horizontal scroll
☐ No view shows raw stack trace, "Error:", `undefined`
☐ Every empty / error / blocked state has friendly copy + 1 next step

PERFORMANCE + ACCESSIBILITY
☐ Lighthouse desktop ≥ 90/90/90/90 on /, /login, /app/researcher
☐ axe-core 0 errors on every route
☐ Initial bundle gz < 250 KB
☐ Tab order works; focus ring visible; "/" focuses query input

SECURITY + AUDIT
☐ RT-01..RT-25 all BLOCKED on live API
☐ verify_chain() = (True, [], full N events)
☐ pytest tests/ -n auto green in < 15 min
☐ 10-step Playwright walk: walk_recording.mp4 exists + 10 PNGs
```

When every box is true, walk the laptop yourself once. If you can answer "I can show this to senior IIT-GN faculty right now" at every screen, the artefact is ready.

---

## 18. Quick Reference for Agents

```
Repo:           ~/Desktop/NRG
Python:         3.11 (.venv/)
Backend:        FastAPI · src/api/main.py · :8000
Frontend:       React+Vite · frontend/ · :5173 (proxies to :8000)
Database:       PostgreSQL prod / SQLite dev · 58 tables
Vector:         Qdrant · :6333 · collection nrg_research
Cache:          Redis · :6379 · 300 s TTL
Orchestration:  LangGraph · src/orchestration/graph.py
Auth:           JWT RS256 · src/auth/jwt_handler.py · HttpOnly cookie
LLM:            LLM_PROVIDER=minimax · model minimax-m2.7
                fallback nvidia · src/config/llm_config.py
Local SLM:      src/config/local_llm.py
PII / inj:      src/security/gateway/prompt_sanitiser.py
Audit:          src/audit/__init__.py · .audit/chain.jsonl
Skills:         src/skills/text_to_sql/ + src/skills/rag/
State:          src/orchestration/state.py · NRGState
Pipeline:       receiver → planner → router → executor → synthesizer → verifier → END
Design tokens:  frontend/src/styles/tokens.css
12 atoms:       frontend/src/components/ui/{Button,Input,...}.tsx
8 screens:      frontend/src/views/AnswerEngine.tsx + Researcher/Government/Industry dashboards + Audit/Settings routes
Test users:     researcher@iitgn.ac.in / Researcher@2026 (T1)
                ministry@nrg.gov.in    / Ministry@2026   (T2)
                partner@industry.in    / Industry@2026   (T3)
Single command: bash scripts/run_critical_path_final.sh
```

---

## 19. The Opportunity

**What we have**: massive curated dataset (rare) + institutional backing (rare) + government funding (very rare) + working sovereign-AI stack (rarer still).

**What we're building**: sovereign AI infrastructure for India's research ecosystem — Indian-soil, DPDP-compliant, audit-bound, fast, beautiful, undeniable.

**The goal**: a professor opens a browser, logs in, types one ambiguous question in plain English, and in under 6 seconds receives a 4-paragraph cited answer with a confidence pill, a tier-aware RBAC view, and a one-click audit trail — all without a single byte of the 600 GB leaving Indian servers.

**Whoever defines the architecture controls the project. This file is that architecture.**

— end of Core_Idea_Clean.md

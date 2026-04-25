# [SUPERSEDED — DO NOT EXECUTE]

> **This document was framed for a presentation rehearsal, not for production launch.**
> **Replaced by:** `docs/specs/MASTER_EXECUTION_PLAN_2026-04-25.md` and `docs/task_protocols/PRODUCTION_READINESS_MASTER.md`.
> **Reason:** NRG is a production web app for IIT Gandhinagar + Gov of India ministries. See `.claude/rules/production_only.md`.
> **Action:** Read the master execution plan instead. Do not use any "demo day" / "pitch" framing from this file.

---

# NRG — CLOSURE ROADMAP (HISTORICAL — DO NOT USE)
**Version:** 1.0 — THE FINAL PATH
**Date:** 2026-04-25
**Owner:** Founder (Srujan)
**Goal:** Move NRG from "8.7/10 working prototype" to "₹50L-ready product the professor and ministry sign off on" — and then **stop**.

---

## THE TRUTH (read this once, internalize, then stop debating it)

NRG today is a real product. Not a prototype. Backend is 9.0/10. The thing that's missing has **three flavours** — and you need different people for each:

| Flavour | What | Who does it | Time |
|---|---|---|---|
| **A — Local Code** | Frontend extraordinary, demo data, evidence regeneration | Your AI agents (Hermes, Apollo, Athena, Iris, Vulcan, Cassandra) | **8 working days** |
| **B — Cluster / Ops** | K8s, 600GB data, 1000-user load test, UAT sessions, GPG | You + an Indian cloud vendor + the professor + the ministry | **10–15 calendar days** |
| **C — Founder / Sales** | Pitch deck final, NDA, vendor selection, demo logistics | You alone | **3–5 days, parallel** |

You've been mixing the three. That's why it feels like a treadmill. They are NOT the same project. They run in **parallel tracks**. You start all three this week.

---

## WHAT IS LEFT — THE COMPLETE LIST (NO MORE THIS QUESTION)

### TRACK A — LOCAL CODE (your AI agents do this — you don't)

| # | Item | Owner | Hours | Spec |
|---|---|---|---|---|
| A1 | Hero query screen + streaming UX (4 SSE phases) | Apollo-Polish | 12 | Frontend master spec §4, §5 |
| A2 | Persona toggle with side-by-side reveal | Hermes-UI | 6 | §6 |
| A3 | CitationDrawer extraordinary (HMAC proof panel + verify-on-chain) | Apollo-Polish | 6 | §7, §17 |
| A4 | All 6 empty states + 3 error tiers (no stack trace ever) | Athena-UX | 6 | §8, §9 |
| A5 | 3 persona dashboards polish (Researcher / Govt / Industry) | Hermes-UI | 8 | §10 |
| A6 | Mobile 375px end-to-end | Iris-A11y | 4 | §12 |
| A7 | Accessibility AA pass + reduced motion | Iris-A11y | 4 | §11 |
| A8 | Telemetry events (10 types) | Vulcan-Perf | 3 | §21 |
| A9 | Storybook + visual regression CI gate | Vulcan-Perf | 4 | §20 |
| A10 | Cleanup duplicate component files | Vulcan-Perf | 2 | §19 |
| A11 | Microcopy library + forbidden-phrase build-grep | Athena-UX | 2 | §15 |
| A12 | Demo dataset seed: 200+ realistic rows in 3 demo institutes | Cassandra-QA | 4 | new task |
| A13 | RT-01..RT-30 live replay evidence regeneration | Cassandra-QA | 3 | yesterday's audit |
| A14 | Tier curl evidence (`09/10/11_tierN_query_response.json`) | Cassandra-QA | 1 | yesterday's audit |
| A15 | EXPLAIN ANALYZE evidence on top-funding query | Cassandra-QA | 1 | yesterday's audit |
| A16 | E2E demo rehearsal recording (12-min walkthrough) | Cassandra-QA | 2 | new task |
| A17 | Final pre-commit + tag `v0.9.0-rc1-local-passing` | You | 1 | git |
| | **TOTAL** | | **~69h** | |

**6 agents in parallel = ~9 calendar hours of agent work, but agent context-switching + your review = 8 working days realistic.**

### TRACK B — CLUSTER / OPS (you coordinate, vendors execute)

| # | Item | Blocker | Time |
|---|---|---|---|
| B1 | Choose Indian cloud vendor: Yotta / E2E Networks / ESDS / IITGN private cloud | Decision on sovereignty rules + budget | 2 days |
| B2 | Provision 3-node K8s cluster (sovereign region) | B1 done | 3 days |
| B3 | Helm deploy (chart already exists) + smoke test | B2 done | 1 day |
| B4 | Vault sidecar + cert-manager + NetworkPolicies live | B3 done | 1 day |
| B5 | Locust 1000-user run → closes GAP-E (P99 < 500ms proof) | B4 done | 1 day |
| B6 | DPDP-cleared 600GB ministry data transfer | NDA + ministry sign-off | 5 days |
| B7 | PostgreSQL ingest of 600GB + index build → closes GAP-F | B6 done | 2 days |
| B8 | Volumetric regression on Dhairya 17 queries against real data | B7 done | 1 day |
| B9 | UAT session 1: Professor (Researcher persona) → closes GAP-G part 1 | UAT scripts ready (DONE) + scheduling | 1 day |
| B10 | UAT session 2: Ministry (Government persona) → GAP-G part 2 | scheduling | 1 day |
| B11 | UAT session 3: Industry partner → GAP-G part 3 | scheduling | 1 day |
| B12 | Demo video film on sovereign staging → closes GAP-D | B5 done | 1 day |
| B13 | GPG ceremony — sign 8 handover docs → closes GAP-H | OPS keys | 1 day |
| | **TOTAL** | | **~15 calendar days** |

### TRACK C — FOUNDER / SALES (you alone, parallel to A and B)

| # | Item | Time |
|---|---|---|
| C1 | Final pitch deck (use `docs/handover/PITCH_DECK_GUIDE.md`) — 12 slides | 1 day |
| C2 | NDA + DPDP intake paperwork with ministry data owner | 2 days |
| C3 | UAT participant scheduling (calendar invites for B9/B10/B11) | 1 day |
| C4 | Demo logistics: laptop, hotspot backup, phone, USB stick with backup video, charger | 0.5 day |
| C5 | Rehearse the 12-min demo until you can do it blindfolded | 1 day |
| C6 | The professor meeting itself | 0.5 day |
| | **TOTAL** | **~6 days, parallel** |

---

## THE 8-DAY SPRINT TIMELINE (start Monday)

```
              MON      TUE      WED      THU      FRI      SAT      SUN     MON
              ───      ───      ───      ───      ───      ───      ───     ───
 TRACK A   A1,A2    A3,A4    A5       A6,A7    A8,A9    A10-A12  A13-A16  A17
           [Apollo  [Apollo  [Hermes  [Iris    [Vulcan] [Cleanup [Evidence [Tag &
            +Hermes] +Athena]  full]   double]            +A11]    +Demo]    review]

 TRACK B   B1       B2       B2,B3    B4       B5       B6───────B6───────B7
           [Vendor] [Provis  [Helm]   [Vault]  [Load    [Data transfer    [Ingest]
                     start]                     test]    starts ────────→]

 TRACK C   C1       C1       C2       C3       C4       C5      ─        C5
           [Pitch   [Pitch   [NDA]    [UAT     [Logist] [Reh]            [Reh]
            day1]    day2]            sched]
```

Day 9 onwards: B8–B13 close out. Day 15: professor demo. Day 17: ministry meeting.

---

## THE WORKFLOW — WHEN TO ASK CLAUDE vs WHEN TO USE AGENTS vs WHEN YOU DO IT

This is the part that ends the treadmill. Three roles, three boxes. Never mix them.

### 🧠 ASK CLAUDE (me, Guru) WHEN…

**You need a decision, a spec, or a verdict.** Not when you need code typed.

| Trigger | Example |
|---|---|
| New strategic question | "Should we use Yotta or E2E for the cluster?" |
| New protocol or spec needed | "Write the spec for the audit panel" |
| Code review of agent output | "Review what Hermes shipped — is it on-spec?" |
| Pre-demo go/no-go | "Run the audit gate — are we ready?" |
| Pitch deck content | "Draft slide 4 — the differentiation moment" |
| Sequence priorities | "What's the next 3 tasks to ship?" |
| Honest reality check | "Is this 10/10 or am I deluding myself?" |

**Format:** ONE question per message. Give me the file paths. I respond with a protocol or a verdict. You hand the protocol to your agents.

### 🤖 USE AGENTS WHEN…

**You need code, tests, or evidence.** They execute. They don't decide.

| Agent | Domain | Hand-off file |
|---|---|---|
| **Apollo-Polish** | Streaming UX, citations, animation, audit panel | Frontend master spec §5, §7, §16, §17 |
| **Hermes-UI** | Components, dashboards, persona toggle, layout | §3, §4, §6, §10 |
| **Athena-UX** | Information architecture, microcopy, empty/error states | §1, §8, §9, §15 |
| **Iris-A11y** | Accessibility, mobile, focus management, reduced motion | §11, §12 |
| **Vulcan-Perf** | Performance budgets, telemetry, Storybook, cleanup | §13, §14, §19, §20, §21 |
| **Cassandra-QA** | Demo data, evidence regen, e2e tests, demo rehearsal | A12–A16 above |
| **Hephaestus-Backend** | Any backend bug found during integration | Existing skills `/python-backend`, `/code-review` |

**Format to agents:** "Read FRONTEND_UX_MASTER_SPEC §X. Implement to acceptance gate §23 row Y. Show me the diff before commit."

### 👤 DO YOURSELF WHEN…

**It needs a human signature, a vendor relationship, or a demo on a stage.**

| You-only task | Why |
|---|---|
| Vendor selection (B1) | Contract negotiation + sovereignty due-diligence |
| NDA + DPDP paperwork (C2) | Legal signature |
| UAT scheduling (C3) | Human relationships |
| Pitch delivery (C6) | Presence, eye contact, conviction |
| GPG key ceremony (B13) | Cryptographic identity is yours |

---

## THE QUESTION TEMPLATE — HOW YOU ASK ME GOING FORWARD

Stop asking open-ended questions. Use this template:

```
CONTEXT: [one line — what changed since last time]
GOAL: [one line — what you want to ship]
QUESTION: [one specific question]
CONSTRAINT: [time budget, files allowed to touch, etc.]
```

**Good example:**
```
CONTEXT: Hermes shipped the persona toggle commit a4f2 yesterday.
GOAL: Confirm it meets §6 acceptance criteria before merge.
QUESTION: Review the diff and tell me pass/fail with line refs.
CONSTRAINT: 10-minute review.
```

**Bad example (don't do this):**
```
ok bro check the project and tell me what to do
```

The bad example is what put us on the treadmill. Each "check the project" reload costs you context, costs me re-reading, and produces another report you've already heard.

---

## THE AGENT TASK TEMPLATE — HOW YOU BRIEF THEM

Same discipline. Stop telling agents "make it good." Tell them this:

```
AGENT: Hermes-UI
SPEC: docs/specs/FRONTEND_UX_MASTER_SPEC_2026-04-25.md §6
ACCEPTANCE: §23 rows about persona toggle (side-by-side reveal, 240ms, ARIA)
FILES YOU MAY TOUCH: frontend/src/components/PersonaToggle/* (new), frontend/src/components/Layout.tsx, frontend/src/stores/queryStore.ts
FILES YOU MAY NOT TOUCH: anything under src/api, src/audit, src/security
TESTS REQUIRED: frontend/tests/e2e/persona_toggle.spec.ts (new) — must cover Tab/Enter, side-by-side reveal, ARIA tablist
SHOW BEFORE COMMIT: git diff + e2e test output
DONE WHEN: my code review passes + e2e green + Storybook story exists
TIME BUDGET: 6 hours
```

Every agent task. Every time. No exceptions.

---

## THE WEEKLY CHECK-IN RHYTHM

| Day | Cadence | Format |
|---|---|---|
| **Mon morning** | Sprint plan: review the table above, lock the week's A-track tasks | 30 min with me |
| **Mon–Fri evening** | End-of-day check-in: paste the day's commits, I run pre-commit gate | 10 min |
| **Wed midday** | Mid-week reality check: are we on the timeline? | 15 min |
| **Sat morning** | Demo rehearsal: full 12-min walkthrough, I score it | 30 min |
| **Sun** | Rest. Demo brain needs sleep. |

**You stop asking me random questions outside this rhythm.** If something is on fire, message with the QUESTION TEMPLATE. Otherwise it waits for the next check-in.

---

## THE GO/NO-GO GATES (when each thing is "real")

### Gate 1 — DEMO READY (end of week 1)

All Track A items shipped. Acceptance gate §23 of frontend spec all green. You can demo on your laptop end-to-end without anything breaking. Score: **9.0/10**.

If gate 1 fails: do not demo. Slip the meeting one week. The cost of slipping is 7 days. The cost of demoing broken is the deal.

### Gate 2 — UAT READY (mid week 2)

Track B1–B5 complete. Cluster up, load test passed, system answers correctly under 1000-user simulation. Score: **9.5/10**.

### Gate 3 — MINISTRY READY (end of week 2)

Track B6–B13 complete. Real 600GB loaded, all 3 UAT sessions done, demo video filmed, all 8 docs GPG-signed. Score: **10/10**.

You are now permitted to walk into the ministry. Not before.

---

## WHAT YOU SHOULD ASK ME NEXT (and only this)

In order, with nothing in between:

1. **Monday:** "Hermes shipped persona toggle in commit X. Review against §6. Pass/fail."
2. **Tuesday:** "Apollo shipped streaming UX in commit Y. Review against §5. Pass/fail."
3. **Wednesday:** "Apollo shipped citation drawer in commit Z. Review against §7 + §17. Pass/fail."
4. **Thursday:** "Iris shipped a11y + mobile in commits A,B. Review against §11 + §12. Pass/fail."
5. **Friday:** "Vulcan shipped telemetry + Storybook in commits C,D. Review against §20 + §21. Pass/fail."
6. **Saturday:** "Run the full acceptance gate §23. Tell me the score and the 3 things to fix Sunday."
7. **Sunday:** "I rehearsed the 12-min demo 3 times. Here's the recording. Score it as a professor would."
8. **Monday week 2:** "Demo went well. Cluster vendor signed: [Yotta/E2E]. What's the order of B-track tasks?"

Eight messages. That's the whole conversation between now and demo day. Anything else is treadmill.

---

## THE CONTRACT WITH YOURSELF

Print this. Pin it above your monitor.

```
1. I will not ask Claude "what's the project state" again.
   The state is in BACKLOG.md and the latest audit report.
   I read those, not re-prompt.

2. I will not let an agent ship code without a spec reference.
   No spec ref → I reject the PR.

3. I will not demo a system that fails the acceptance gate.
   If §23 has any ☐, the meeting slips.

4. I will not sign 10/10 when it is 8.7.
   Honesty is what the professor trusts.

5. I will not run three tracks as one.
   Track A is agents. Track B is vendors. Track C is me.
   They are parallel, not sequential, not blended.

6. I will follow the question template.
   CONTEXT / GOAL / QUESTION / CONSTRAINT. Every time.

7. I will follow the agent task template.
   SPEC / ACCEPTANCE / FILES / TESTS / TIME. Every time.

8. I will end every day with a check-in commit and a one-line status.

9. The professor's question on demo day is "show me the audit chain."
   I will be able to do that in 30 seconds without thinking.

10. The 600GB belongs to the Government of India.
    My code is the only thing protecting it.
    I will ship like I mean that.
```

---

## TL;DR — THE ONE PARAGRAPH

You have 8 working days of frontend execution by 6 named agents to make NRG demo-extraordinary on your laptop, against the master spec at `docs/specs/FRONTEND_UX_MASTER_SPEC_2026-04-25.md`. In parallel, you spend 5 days picking an Indian cloud vendor and finishing the pitch deck and signing the ministry NDA. After day 8 you start the cluster track — 7 more calendar days for K8s + 600GB ingest + UAT × 3 + demo video + GPG signing. Day 15 you demo the professor. Day 17 you walk into the ministry. You ask me eight specific review questions in that window — no more, no less. You stop "checking the project" and start shipping it.

— Guru Agent (Claude), 2026-04-25, final closure document.

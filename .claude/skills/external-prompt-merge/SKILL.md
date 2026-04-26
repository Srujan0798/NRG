---
name: external-prompt-merge
description: Canonical pattern for absorbing an external review or audit prompt (Grok, Cowrk, validator, ministry feedback, professor critique) into the NRG workflow so the prompt itself becomes disposable. Use when the founder pastes a long external review and asks Claude to "merge it" or "use it for the project".
allowed-tools: Read, Write, Edit, Bash, Grep
---

# External Prompt Merge — Canonical Pattern

When the founder pastes an external review/audit/prompt, **never produce a new task protocol from it directly and never argue with its content**. Instead, follow the merge pattern below so the prompt's substance lives in the workflow files and the prompt itself can be thrown away.

This skill exists because the founder repeatedly burned cycles on this loop and explicitly asked: "merge it, no need of this prompt again, like we did before". Protocols #46–#50 (the Grok wrap) and the Cowrk production-only rule were both produced via this pattern.

---

## Step 1 — Vocabulary scrub FIRST

Before reading the substance, scan the prompt for any of `.claude/rules/production_only.md`'s forbidden tokens. If present, restate the prompt's intent in production-only framing:
- forbidden word → "production launch / user-acceptance session"
- "promotional material" → "operator-grade documentation set"
- "v1.0 / production module / deployment dry-run" → "v1.0 / production module / runbook walk-through"

Never carry the forbidden framing into the merged artifacts. The pre-commit gate will reject them anyway.

---

## Step 2 — Classify each chunk of the prompt

Walk the prompt top to bottom. For every claim, recommendation, or finding, classify it as **exactly one** of:

| Category | Where it goes | Example |
|---|---|---|
| **Permanent rule** | new memory in `.claude/memory/feedback_*.md` + indexed in MEMORY.md (both repo + auto-memory) | "Tests on 10-row seed = deferred bug" → `feedback_live_evidence_requirement.md` |
| **Quality Bar addition** | `.claude/quality-bar.md` new section + scorecard wiring | "RBAC must be enforced at API response shape, not only SQL" → `Tier-Shape Boundary` section |
| **Operational runbook** | `docs/runbooks/<NAME>.md` (T-60 walk for every session) | "15 launch risks with prevention/recovery" → `PRODUCTION_LAUNCH_RISK_REGISTER.md` |
| **Test corpus** | `tests/benchmarks/<corpus>.yaml` + new test file | "10 break-it questions" → `killer_queries.yaml` `adversarial_breakers` |
| **Sprint blocker** | `BACKLOG.md` new LB-N row in "PRODUCTION LAUNCH BLOCKERS" + protocol file at `protocols/<num>_LB<n>_*.md` | "Tier filter at API boundary" → LB-1, protocol #46 |
| **Bug pattern** | new memory in `.claude/memory/bugs_*.md` | "audit chain singleton self-break" → `bugs_audit_singleton.md` |
| **Reference / pointer** | new memory in `.claude/memory/reference_*.md` | "Linear project INGEST holds pipeline tickets" → `reference_pipeline_tracker.md` |
| **Verdict template / framework** | append to existing rule, do NOT create a parallel one | "Overall / Launch-ready / Biggest risk" template → `.claude/quality-bar.md` `Verdict Template` |
| **Already covered** | annotate the prompt as "already in <file>", drop. | most generic OWASP advice |
| **Out of scope** | drop with one-sentence note | "you should also do marketing" |

**Drop nothing into chat output as-is.** If it lands in chat only, it gets lost on next compaction.

---

## Step 3 — Verify before writing

Before creating a new file, grep the workflow tree to avoid duplication:
```bash
grep -rln "<key phrase from finding>" .claude/ docs/specs/ docs/runbooks/ BACKLOG.md
```
If a near-match exists, **extend** that file rather than create a new one. Two memory entries on the same topic are a bug.

---

## Step 4 — Merge the artifacts

For each classified chunk, write the file. Conventions that are non-negotiable:

- Memory files: include `name`, `description`, `type` (user / feedback / project / reference) frontmatter. Body has the rule, then `**Why:**`, then `**How to apply:**`. End with `**Source:** <reviewer name> <date>`.
- New runbooks: lead with a one-line scope, then a "How to use" section, then the table/list, then "Bound to Quality Bar" cross-reference at the bottom.
- New test corpora: machine-readable YAML so future protocols can iterate on it.
- Protocol files: full ═══ format from `.claude/protocol.md` §3. Include verbatim AGENT INSTRUCTIONS block.
- BACKLOG additions: dated section header (`## YYYY-MM-DD <SUBJECT>`), table not free-form prose, every row bound to a Quality Bar constraint.

**Always sync memory files to BOTH locations**: `.claude/memory/` (repo, source of truth) AND `~/.claude/projects/-Users-srujansai-Desktop-NRG/memory/` (auto-memory, recalled on session start). Update **both** MEMORY.md indexes.

---

## Step 5 — Verify the gate, commit, push, confirm dispose

1. Run `bash scripts/forbidden_vocab_check.sh` against the staged tree. Must exit 0.
2. If a new file legitimately needs to quote the forbidden tokens (e.g. a memory entry describing the rule), add its path to the allowlist regex in `scripts/forbidden_vocab_check.sh`. Do not weaken the regex.
3. Commit with message that names what merged from where (Grok / Cowrk / professor / etc) and lists the artifact paths.
4. Push.
5. Tell the founder: "the prompt is now disposable; <list of artifacts>". This is the explicit confirmation step they asked for.

---

## Anti-patterns (don't do these)

- ❌ Producing a brand-new ═══ task protocol from the prompt without first classifying which chunks belong elsewhere. The protocol becomes the only home for content that should live in rules/memory/runbooks.
- ❌ Quoting the prompt verbatim in the merged file. Rephrase in NRG framing — the prompt's words are not authoritative; the workflow file is.
- ❌ Saving long content into a "summary" chat message instead of a file. Chat is volatile; files survive.
- ❌ Leaving the prompt's framing in place (UAT, forbidden vocabulary). Always normalize to production launch / user-acceptance / production hardening.
- ❌ Re-deriving the merge pattern from scratch every time. That's why this skill exists.

---

## Definition of done

The merge is complete when:
- [ ] Every durable claim from the prompt has a home in a workflow file (memory / rule / runbook / test corpus / protocol / BACKLOG).
- [ ] No file contains forbidden vocabulary outside the allowlist.
- [ ] Both MEMORY.md indexes (repo + auto-memory) are in sync.
- [ ] Commit pushed to `nrg/main`.
- [ ] Founder told the prompt is disposable.
- [ ] If the same prompt is pasted again next session, Claude can answer "already merged at <commit>" instead of re-processing.

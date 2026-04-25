# TP-C1 — External AI Audit Execution

**Owner:** GURU (Founder/You) — This is a meta-task, not for execution agents  
**Estimated Duration:** 1 day setup + wait for AI responses  
**Blockers:** None  
**Reference:** `.claude/rules/audit_protocol.md` Section 13 + `.claude/skills/external-audit/SKILL.md`

---

## Objective

Run the Universal AI Audit Master Prompt on 3+ independent AIs. Collect their 8 deliverables each. Merge gap lists. The union of all gaps found = your real gap list. Fix what they find before the professor does.

---

## Fortify Phase (Gather Files)

Collect exactly these 4 files:

| File | Path | Verify Exists |
|------|------|---------------|
| Core Idea | `Core_Idea_Clean.md` | `ls Core_Idea_Clean.md` |
| Schema | `db_struct.sql` | `ls db_struct.sql` |
| Backlog | `BACKLOG.md` | `ls BACKLOG.md` |
| Dhairya Audit | `docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` | `ls docs/reports/SQL_AUDIT_REPORT_DHAIRYA.md` |

Optional 5th: Latest self-audit report from `evidence/<date>/20_self_audit_report.md`

If any file is missing or outdated, update it first.

---

## Elevate Phase (Run on 3+ AIs)

### Step 1: Copy the Prompt

Open `.claude/rules/audit_protocol.md` Section 13.6. Copy the entire prompt template.

### Step 2: Choose 3+ AIs

Recommended set:
- Claude (Anthropic) — best at technical analysis
- GPT-4 (OpenAI) — best at finding edge cases
- Gemini (Google) — best at questioning assumptions
- Grok (xAI) — best at adversarial thinking

Minimum: 3. More is better.

### Step 3: Run Each AI

For each AI:
1. Open a fresh conversation
2. Upload the 4 files as attachments
3. Paste the prompt template from Section 13.6
4. Wait for complete response (2,000–4,000 words)
5. Verify all 8 deliverables are present
6. Save the full response to:
   ```
   evidence/2026-04-25/external_audit/ai_<name>_response.md
   ```

### Step 4: Extract Deliverable 7 (Gap Lists)

From each AI response, extract every GAP entry:

```
GAP-[X]: [Name]
Location: [File path]
Root cause: [Why]
Fix required: [Exact fix]
Test: [Test to run]
Time estimate: [Duration]
Blocks demo: YES / NO
```

### Step 5: Merge and Deduplicate

Create master gap list:
```markdown
# Master Gap List — External Audit 2026-04-25

## All Gaps (Union of N AI Audits)
| Gap ID | Name | Found By | Location | Blocks Demo | Time | Status |
|--------|------|----------|----------|-------------|------|--------|

## By Agreement Level
### All AIs Agree (Fix Immediately)
...

### 2/3 AIs Agree (Investigate Seriously)
...

### 1/3 AIs Only (Verify Carefully)
...
```

### Step 6: Sort by Impact

Sort the merged list:
1. All gaps marked "Blocks Demo: YES" first
2. Then by time estimate (quickest fixes first)
3. Then by agreement level (all AIs agree = higher priority)

---

## Immortalize Phase (Evidence)

1. All AI responses:
   ```
   evidence/2026-04-25/external_audit/ai_claude_response.md
   evidence/2026-04-25/external_audit/ai_gpt4_response.md
   evidence/2026-04-25/external_audit/ai_gemini_response.md
   ```

2. Master gap list:
   ```
   evidence/2026-04-25/external_audit/C1_master_gap_list.md
   ```

3. Comparison matrix:
   ```
   evidence/2026-04-25/external_audit/C1_agreement_matrix.md
   ```
   Show which AI found which gap.

---

## Acceptance Criteria

- [ ] 3+ AI responses collected, all 8 deliverables present in each
- [ ] Master gap list created with all gaps deduplicated
- [ ] Agreement level classified for every gap
- [ ] Gaps sorted by "Blocks Demo" + time estimate
- [ ] Master gap list is actionable — each gap has location, fix, test, time

---

## What To Do With The Output

1. **All 3 AIs agree on a gap** → Add to sprint backlog as P1. Do not debate.
2. **2/3 AIs agree** → Investigate. Likely real. Run the test they suggest.
3. **Only 1 AI found it** → Verify with evidence. Either valuable find or hallucination.
4. **None found it but you know it's broken** → Add it yourself. AI audits are not omniscient.

The merged gap list becomes your next sprint backlog. Do not argue with the gaps. Fix them. Then re-run the external audit. If the AI no longer flags the gap — it is fixed.

---
name: Export Data Integrity
description: CSV/XLSX exports must preserve the tier-filtered result shape, row count, dates, identifiers, and audit trace
type: feedback
---

NRG exports are part of the product trust boundary. A CSV or future XLSX file
must be as tier-safe and auditable as the rendered answer.

**Rule:**

1. Export only the currently rendered, tier-filtered result set. Same filters,
   same row count, same allowed columns, and no hidden raw backing fields.
2. Tier 3 exports must contain no PII keys, PII values, or small-cohort
   identifying details. Prove this from the file content, not the UI.
3. Preserve long IDs, grant IDs, phone-like values, ZIP/PIN-like values, and
   leading-zero values as text so spreadsheet tools cannot silently corrupt
   them.
4. Export dates in an explicit stable format. Include timezone when timezone
   affects interpretation.
5. Attach traceability: query text, tier, audit event ID, source row count, and
   generated-at timestamp should be visible in the export metadata or adjacent
   evidence.
6. If XLSX output is added later, keep formulas live only when the user needs a
   live workbook. Otherwise prefer static, auditable values. Inspect for formula
   errors such as `#REF!`, `#DIV/0!`, `#VALUE!`, and `#NAME?` before acceptance.

**Why:** Spreadsheet tools can silently mangle identifiers, dates, and numeric
precision. More importantly, export/download paths can bypass visual tier
filtering if treated as a secondary feature.

**How to apply:**

- Main-flow tests must inspect at least one export file for row count, headers,
  tier scope, dates, identifiers, and audit trace.
- Evidence folders should keep exported files under `evidence/YYYY-MM-DD/exports/`
  with a short integrity check note.
- Do not install a broad Excel skill unless NRG starts producing complex
  workbook artifacts. Keep the current rule focused on app result exports.

**Source:** MiniMax `excel-xlsx` reviewed 2026-04-29; kept as export integrity
discipline, not as a standalone spreadsheet skill.

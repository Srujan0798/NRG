---
name: synthesize-research
description: Synthesize user research from interviews, surveys, and feedback into structured insights. Use when you have a pile of interview notes, survey responses, or support tickets to make sense of, need to extract themes and rank findings by frequency and impact, or want to turn raw feedback into roadmap recommendations.
---

# /synthesize-research

Synthesize user research from interviews, surveys, and feedback into structured insights.

## Usage

```
/synthesize-research <research data or topic>
```

## When to Use

- Making sense of interview notes, survey responses, or support tickets
- Extracting themes and ranking by frequency and impact
- Turning raw feedback into roadmap recommendations

## Workflow

1. **Ingest data** — Paste notes, upload transcripts, or summarize findings
2. **Extract themes** — Group related observations into buckets
3. **Quantify** — Count frequency of each theme
4. **Rank by impact** — High frequency + high severity = top priority
5. **Draft insights** — Write concise findings with supporting evidence
6. **Recommend actions** — Link insights to roadmap items

## Output Format

```markdown
# Research Synthesis: [Topic]

## Methodology
- [N] interviews / [N] survey responses / [N] tickets
- Date range: [Dates]

## Key Themes
| Theme | Frequency | Severity | Insight |
|-------|-----------|----------|---------|
| [Theme] | [N] | High/Med/Low | [One-liner] |

## Verbatim Quotes
> "[Quote]" — [Participant type]

## Recommendations
1. [Action] → [Roadmap item]
```

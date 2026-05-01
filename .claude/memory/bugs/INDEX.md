# Bug Registry

Known bugs, their root causes, and permanent fixes. Every bug here has a lesson that prevents recurrence.

| Bug | Severity | Status | Lesson |
|-----|----------|--------|--------|
| [audit-binding-rebuild-after-validation](audit-binding-rebuild-after-validation.md) | High | Mitigated | Verify per-user binding after live validation; continuity-only checks are insufficient |
| [audit-singleton](audit-singleton.md) | High | Fixed | Rebuild scripts must reset BOTH AuditLog singletons or chain self-breaks |
| [c4-rate-limit-counted-as-success](c4-rate-limit-counted-as-success.md) | High | Fixed | C4 load evidence must fail 429s and expose per-workload `/query` metrics |
| [frontend-crashes](frontend-crashes.md) | High | Fixed | ThemeProvider, hooks-in-effects, string-vs-array API fields |
| [patterns](patterns.md) | Critical | Ongoing | Master list of recurring bug patterns across the codebase |
| [postgres-identifier-limit](postgres-identifier-limit.md) | Medium | Fixed | 62-char column names crash LLM-emitted aliases |
| [silent-wrong-answer](silent-wrong-answer.md) | Critical | Mitigated | Biggest failure mode: confident wrong answers on ambiguous queries |
| [skill-md-deletions](skill-md-deletions.md) | Low | Guarded | Restore unstaged SKILL.md deletions immediately |
| [venv-pytest-blocker](venv-pytest-blocker.md) | High | Fixed | Broken `.venv` symlink + router-eval stall prevents full pytest |

---

**When to add:** After any bug fix that revealed a systemic pattern.
**Format:** `what-went-wrong → root-cause → permanent-fix → prevention-check`

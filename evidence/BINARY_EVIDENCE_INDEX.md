# Binary Evidence Index

Date updated: 2026-05-05

## Policy

Binary screenshots and recordings are evidence, so historical paths should keep
resolving. Exact duplicate binaries are archived by replacing older files with
relative symlinks to the latest identical artifact instead of deleting the path.

## Latest Canonical Duplicate Targets

| Canonical artifact | Older duplicate paths now linked |
|---|---:|
| `evidence/2026-05-05/maximum_enforcement_local_browser/02_login_desktop.png` | 8 |
| `evidence/2026-05-05/maximum_enforcement_local_browser/03_researcher_dashboard_desktop.png` | 7 |
| `evidence/2026-05-01/glm_fusion_browser_proof/04_glm_query_home_desktop.png` | 1 |

The active May 5 browser-proof directories were not rewritten because they are
part of the current evidence line and were already staged before this cleanup.

## Verification Command

```bash
find evidence -type l -print
find evidence -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webm' -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.gif' -o -iname '*.pdf' \) -print | sort | wc -l
```

#!/usr/bin/env bash
# NRG forbidden-vocabulary check.
# Fails any commit whose CHANGED files contain demo-framing vocabulary.
# With --all: scans ALL tracked and untracked non-ignored files (use before external release).
# NRG is production. See .claude/rules/production_only.md
set -e

FORBIDDEN_PATTERN='\b(demo|demo-ready|demo day|demo video|demo dataset|demo rehearsal|pitch deck|MVP|prototype|works on my machine)\b'

# Allowlist: rule documents and the master execution plan are allowed to MENTION the forbidden words
# (they describe why those words are forbidden).
ALLOWLIST_PATHS='\.claude/rules/production_only\.md|\.claude/rules/external_audit\.md|\.claude/memory/|\.agents/skills/forbidden-vocab-cleanup/SKILL\.md|docs/specs/MASTER_EXECUTION_PLAN_|docs/specs/DISPATCH_|docs/task_protocols/PRODUCTION_READINESS_MASTER\.md|scripts/forbidden_vocab_check\.sh|protocols/[0-9]+_LB[0-9]+_|^BACKLOG\.md$|\.github/workflows/ci\.yml$|frontend/tests/|src/skills/text_to_sql/schema_extractor\.py|src/skills/text_to_sql/sqlite_schema_extractor\.py|evidence/|docs/audits/|docs/CODE_REVIEW\.md|docs/AGENT_AUDIT_PROMPT\.md|docs/ROADMAP\.md|docs/STAKEHOLDER_UPDATE\.md|docs/reports/PROJECT_PLAN\.md|docs/release/RELEASE_SCRIPT\.md|docs/handover/PITCH_DECK_GUIDE\.md|docs/task_protocols/|docs/uat/|docs/specs/MASTER_CLOSURE_|docs/v4\.1_execution/|docs/external_audit/'

# Determine scan mode: changed files (default) or full working tree (--all)
if [[ "${1:-}" == "--all" ]]; then
  CHANGED_FILES="$({ git ls-files; git ls-files --others --exclude-standard; } | sort -u | grep -v -E "$ALLOWLIST_PATHS" || true)"
  SCAN_MODE="full repo"
else
  CHANGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR | grep -v -E "$ALLOWLIST_PATHS" || true)"
  SCAN_MODE="changed files"
fi

if [[ -z "$CHANGED_FILES" ]]; then
  exit 0
fi

# Skip binary, vendor, and lockfile noise.
TARGET_FILES=$(printf '%s\n' $CHANGED_FILES | grep -v -E '\.(json|lock|svg|png|jpg|jpeg|woff2?|ttf|otf|ico|pdf|min\.js|min\.css)$|node_modules/|\.git/|dist/|build/|coverage/|docs/audits/' || true)

if [[ -z "$TARGET_FILES" ]]; then
  exit 0
fi

# Run grep across target files; capture violations.
VIOLATIONS="$(grep -IniE "$FORBIDDEN_PATTERN" $TARGET_FILES 2>/dev/null || true)"

if [[ -n "$VIOLATIONS" ]]; then
  echo "─────────────────────────────────────────────────────────────"
  echo "  FORBIDDEN VOCABULARY DETECTED ($SCAN_MODE)"
  echo "  NRG is production software. See .claude/rules/production_only.md"
  echo "─────────────────────────────────────────────────────────────"
  echo "$VIOLATIONS"
  echo "─────────────────────────────────────────────────────────────"
  echo "  Replace 'demo' → 'release', 'pitch' → 'production capability',"
  echo "  'MVP' → 'v1.0', 'prototype' → 'production module'."
  echo "  Then re-stage and commit."
  exit 1
fi

exit 0

#!/usr/bin/env bash
# NRG forbidden-vocabulary check.
# Fails any commit whose CHANGED files contain demo-framing vocabulary.
# NRG is production. See .claude/rules/production_only.md
set -e

FORBIDDEN_PATTERN='\b(demo|demo-ready|demo day|demo video|demo dataset|demo rehearsal|pitch deck|MVP|prototype|works on my machine)\b'

# Allowlist: rule documents and the master execution plan are allowed to MENTION the forbidden words
# (they describe why those words are forbidden).
ALLOWLIST_PATHS='\.claude/rules/production_only\.md|\.claude/memory/|docs/specs/MASTER_EXECUTION_PLAN_|docs/task_protocols/PRODUCTION_READINESS_MASTER\.md|scripts/forbidden_vocab_check\.sh|protocols/[0-9]+_LB[0-9]+_'

CHANGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR | grep -v -E "$ALLOWLIST_PATHS" || true)"

if [[ -z "$CHANGED_FILES" ]]; then
  exit 0
fi

# Skip binary, vendor, and lockfile noise.
TARGET_FILES=$(printf '%s\n' $CHANGED_FILES | grep -v -E '\.(json|lock|svg|png|jpg|jpeg|woff2?|ttf|otf|ico|pdf|min\.js|min\.css)$|node_modules/|\.git/|dist/|build/|coverage/' || true)

if [[ -z "$TARGET_FILES" ]]; then
  exit 0
fi

# Run grep across changed files; capture violations.
VIOLATIONS="$(grep -InE "$FORBIDDEN_PATTERN" $TARGET_FILES 2>/dev/null || true)"

if [[ -n "$VIOLATIONS" ]]; then
  echo "─────────────────────────────────────────────────────────────"
  echo "  FORBIDDEN VOCABULARY DETECTED"
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

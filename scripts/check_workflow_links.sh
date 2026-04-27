#!/bin/bash
# check_workflow_links.sh — verify every [text](path.md|.sh|.yaml) link in
# .claude/ and .agents/ resolves to an existing file. Exits non-zero on broken refs.
set -e
BAD=0
SCAN_DIRS=(".claude" ".agents")

for dir in "${SCAN_DIRS[@]}"; do
  [ -d "$dir" ] || continue
  while IFS= read -r f; do
    base=$(dirname "$f")
    while IFS= read -r line; do
      target=$(echo "$line" | grep -oE '\(([^)]+\.(md|sh|yaml|yml|json|py))\)' | tr -d '()' | head -1)
      [ -z "$target" ] && continue
      [[ "$target" =~ ^https?:// ]] && continue
      [[ "$target" =~ ^# ]] && continue
      # strip anchor
      target_path="${target%%#*}"
      [ -z "$target_path" ] && continue
      if [ ! -e "$base/$target_path" ] && [ ! -e "$target_path" ]; then
        echo "BROKEN  $f -> $target_path"
        BAD=1
      fi
    done < <(grep -oE '\[[^]]+\]\([^)]+\)' "$f" 2>/dev/null || true)
  done < <(find "$dir" -name "*.md" -type f)
done

if [ "$BAD" -eq 0 ]; then
  echo "workflow link integrity: OK"
fi
exit $BAD

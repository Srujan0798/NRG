#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${FRONTEND_DIR}/.." && pwd)"
BUILD_DIR="${1:-${REPO_ROOT}/dist/frontend}"

if [[ ! -d "${BUILD_DIR}" ]]; then
  echo "Build directory not found: ${BUILD_DIR}" >&2
  exit 1
fi

for phrase in \
  "An error occurred" \
  "Something went wrong" \
  "Please try again later" \
  "0 rows returned" \
  "Internal Server Error" \
  "Network Error" \
  "Error:" \
  "TypeError:"
do
  if grep -RIn --exclude='*.map' -- "${phrase}" "${BUILD_DIR}" >/tmp/nrg_forbidden_phrase_match.txt; then
    echo "Forbidden phrase found: ${phrase}" >&2
    cat /tmp/nrg_forbidden_phrase_match.txt >&2
    exit 1
  fi
done

if grep -RInE --exclude='*.map' -- '(["'"'"'>])undefined(["'"'"'<])|(["'"'"'>])null(["'"'"'<])' "${BUILD_DIR}" >/tmp/nrg_forbidden_phrase_match.txt; then
  echo "Forbidden rendered literal found: undefined/null" >&2
  cat /tmp/nrg_forbidden_phrase_match.txt >&2
  exit 1
fi

echo "Forbidden phrase scan passed for ${BUILD_DIR}"

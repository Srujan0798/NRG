#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${FRONTEND_DIR}/.." && pwd)"
BUILD_DIR="${1:-${REPO_ROOT}/dist/frontend}"
MATCH_FILE="$(mktemp)"

cleanup() {
  rm -f "${MATCH_FILE}"
}
trap cleanup EXIT

if [[ ! -d "${BUILD_DIR}" ]]; then
  echo "Build directory not found: ${BUILD_DIR}" >&2
  exit 1
fi

for phrase in \
  "An error occurred" \
  "Something went wrong" \
  "Please try again later" \
  "0 rows returned" \
  "Internal Server Error"
do
  if grep -RIn --exclude='*.map' -- "${phrase}" "${BUILD_DIR}" >"${MATCH_FILE}"; then
    echo "Forbidden phrase found: ${phrase}" >&2
    cat "${MATCH_FILE}" >&2
    exit 1
  fi
done

for phrase in "Network Error" "Error:" "TypeError:" "Traceback"
do
  if grep -In -- "${phrase}" "${FRONTEND_DIR}/src/i18n/en-IN.ts" "${FRONTEND_DIR}/index.html" >"${MATCH_FILE}"; then
    echo "Forbidden visible-copy phrase found: ${phrase}" >&2
    cat "${MATCH_FILE}" >&2
    exit 1
  fi
done

if grep -InE -- '(["'"'"'>])undefined(["'"'"'<])|(["'"'"'>])null(["'"'"'<])' "${FRONTEND_DIR}/src/i18n/en-IN.ts" "${FRONTEND_DIR}/index.html" >"${MATCH_FILE}"; then
  echo "Forbidden rendered literal found: undefined/null" >&2
  cat "${MATCH_FILE}" >&2
  exit 1
fi

echo "Forbidden phrase scan passed for ${BUILD_DIR}"

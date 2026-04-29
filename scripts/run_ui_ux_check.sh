#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
EVIDENCE_DATE="${NRG_EVIDENCE_DATE:-$(date +%F)}"
EVIDENCE_DIR="${ROOT_DIR}/evidence/${EVIDENCE_DATE}/ui_ux"

mkdir -p "${EVIDENCE_DIR}/after" "${EVIDENCE_DIR}/before"

log() {
  printf '\n[%s] %s\n' "$(date +%H:%M:%S)" "$*"
}

log "1/7 build frontend"
(cd "${FRONTEND_DIR}" && npm run build)

log "2/7 lint and focused component checks"
(
  cd "${FRONTEND_DIR}"
  npm run lint
  npx jest tests/components/AnswerEngineSurface.test.tsx tests/a11y/contrast.test.ts --runInBand
)

log "3/7 axe accessibility walk"
(
  cd "${FRONTEND_DIR}"
  npx playwright test -c tests/playwright.config.ts tests/a11y/axe.test.ts
)
rm -rf "${EVIDENCE_DIR}/axe"
mkdir -p "${EVIDENCE_DIR}/axe"
cp "${FRONTEND_DIR}"/test-results/a11y/*.axe.json "${EVIDENCE_DIR}/axe/"

log "4/7 capture 8 screens at desktop and mobile"
(
  cd "${FRONTEND_DIR}"
  NRG_EVIDENCE_DATE="${EVIDENCE_DATE}" \
  API_TARGET="${API_TARGET:-localhost:8000}" \
  PLAYWRIGHT_RECORD_VIDEO=1 \
  npx playwright test -c tests/playwright.config.ts tests/e2e/ui_ux_walk.spec.ts
)

WALK_VIDEO_LIST="${EVIDENCE_DIR}/.walk_videos.txt"
find "${FRONTEND_DIR}/tests/test-results" -path '*ui_ux_walk*' -name 'video.webm' | sort > "${WALK_VIDEO_LIST}" || true
DESKTOP_VIDEO="$(sed -n '1p' "${WALK_VIDEO_LIST}")"
MOBILE_VIDEO="$(sed -n '2p' "${WALK_VIDEO_LIST}")"
if [[ -n "${DESKTOP_VIDEO}" ]]; then
  cp "${DESKTOP_VIDEO}" "${EVIDENCE_DIR}/walk_recording_desktop.webm"
fi
if [[ -n "${MOBILE_VIDEO}" ]]; then
  cp "${MOBILE_VIDEO}" "${EVIDENCE_DIR}/walk_recording_mobile.webm"
fi
rm -f "${WALK_VIDEO_LIST}"

log "5/7 lighthouse desktop and mobile"
(
  cd "${FRONTEND_DIR}"
  LIGHTHOUSE_EVIDENCE_DIR="evidence/${EVIDENCE_DATE}/ui_ux" npm run lighthouse:desktop
  LIGHTHOUSE_EVIDENCE_DIR="evidence/${EVIDENCE_DATE}/ui_ux" npm run lighthouse:mobile
)

log "6/7 build gallery"
(cd "${ROOT_DIR}" && NRG_EVIDENCE_DATE="${EVIDENCE_DATE}" node scripts/build_before_after_gallery.mjs)

log "7/7 summarize evidence"
find "${EVIDENCE_DIR}" -maxdepth 2 -type f | sort > "${EVIDENCE_DIR}/FILES.txt"
printf 'PASS: UI/UX screenshots and gallery written to %s\n' "${EVIDENCE_DIR}"

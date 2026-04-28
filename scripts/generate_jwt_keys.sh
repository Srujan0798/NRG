#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRIVATE_REL="${JWT_PRIVATE_KEY_PATH:-infrastructure/kong/ssl/jwt_rsa.key}"
PUBLIC_REL="${JWT_PUBLIC_KEY_PATH:-infrastructure/kong/ssl/jwt_rsa.pub}"
PRIVATE_PATH="${ROOT_DIR}/${PRIVATE_REL}"
PUBLIC_PATH="${ROOT_DIR}/${PUBLIC_REL}"

mkdir -p "$(dirname "${PRIVATE_PATH}")" "$(dirname "${PUBLIC_PATH}")"

if [[ ! -s "${PRIVATE_PATH}" ]]; then
  echo "Generating JWT private key: ${PRIVATE_REL}"
  openssl genrsa -out "${PRIVATE_PATH}" 4096 >/dev/null 2>&1
  chmod 600 "${PRIVATE_PATH}"
else
  echo "JWT private key already exists: ${PRIVATE_REL}"
fi

if [[ ! -s "${PUBLIC_PATH}" ]]; then
  echo "Generating JWT public key: ${PUBLIC_REL}"
  openssl rsa -in "${PRIVATE_PATH}" -pubout -out "${PUBLIC_PATH}" >/dev/null 2>&1
else
  echo "JWT public key already exists: ${PUBLIC_REL}"
fi

LEGACY_PUBLIC_PATH="${PRIVATE_PATH}.pub"
if [[ ! -s "${LEGACY_PUBLIC_PATH}" ]]; then
  cp "${PUBLIC_PATH}" "${LEGACY_PUBLIC_PATH}"
fi

echo "JWT keypair ready."

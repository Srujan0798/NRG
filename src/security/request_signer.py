"""HMAC request signing with replay protection for /query endpoint.

Signature: HMAC-SHA256(api_secret, timestamp + request_body)
Rejects requests older than 5 minutes (300 seconds).
Logs all signature validation attempts.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

SIGNATURE_VALIDATION_LOG: list[dict] = []

SIGNATURE_EXPIRY_SECONDS = 300
HEX_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def get_api_secret() -> str:
    return os.getenv("NRG_REQUEST_SIGNING_SECRET", "nrg-default-signing-secret")


def log_signature_attempt(
    identifier: str,
    timestamp: int,
    signature: str,
    valid: bool,
    reason: str = "",
) -> None:
    """Log all signature validation attempts for audit."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "identifier": identifier,
        "request_timestamp": timestamp,
        "signature_prefix": signature[:16] if signature else "",
        "valid": valid,
        "reason": reason,
        "age_seconds": int(time.time()) - timestamp if timestamp else None,
    }
    SIGNATURE_VALIDATION_LOG.append(entry)
    logger.info(
        "Signature validation: identifier=%s valid=%s age=%ss reason=%s",
        identifier,
        valid,
        entry["age_seconds"],
        reason,
    )


class RequestSigner:
    """HMAC-SHA256 request signer with timestamp validation."""

    def __init__(self, secret: Optional[str] = None):
        self._secret = (secret or get_api_secret()).encode()

    def _make_message(self, timestamp: int, body: str) -> bytes:
        return f"{timestamp}:{body}".encode()

    def sign(self, body: str, timestamp: Optional[int] = None) -> str:
        """Generate HMAC signature for a payload."""
        ts = timestamp or int(time.time())
        message = self._make_message(ts, body)
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def verify(self, body: str, timestamp: int, signature: str) -> tuple[bool, str]:
        """Verify HMAC signature with replay protection.

        Returns:
            (valid: bool, reason: str)
        """
        age = int(time.time()) - timestamp

        if age > SIGNATURE_EXPIRY_SECONDS:
            return False, f"Request too old: {age}s > {SIGNATURE_EXPIRY_SECONDS}s"

        if age < -5:
            return False, f"Timestamp in future: {age}s"

        expected = self.sign(body, timestamp)
        malformed = not isinstance(signature, str) or not HEX_SHA256_RE.fullmatch(signature)
        candidate = signature.lower() if not malformed else "0" * len(expected)
        if not hmac.compare_digest(expected, candidate):
            return False, "Malformed signature" if malformed else "Signature mismatch"

        return True, "OK"

    def sign_payload(self, payload: dict) -> dict:
        """Create signed payload with timestamp."""
        timestamp = int(time.time())
        body_str = json.dumps(payload, sort_keys=True, default=str)
        signature = self.sign(body_str, timestamp)
        return {
            **payload,
            "_timestamp": timestamp,
            "_signature": signature,
        }


_signer_instance: Optional[RequestSigner] = None


def get_signer() -> RequestSigner:
    global _signer_instance
    if _signer_instance is None:
        _signer_instance = RequestSigner()
    return _signer_instance


def verify_hmac_signature(
    body: str,
    timestamp: int,
    signature: str,
    identifier: str = "unknown",
) -> bool:
    """Verify HMAC signature and log the attempt.

    Returns True if valid, False otherwise.
    """
    signer = get_signer()
    valid, reason = signer.verify(body, timestamp, signature)

    log_signature_attempt(
        identifier=identifier,
        timestamp=timestamp,
        signature=signature,
        valid=valid,
        reason=reason,
    )

    if not valid:
        logger.warning(
            "HMAC signature verification failed: identifier=%s reason=%s",
            identifier,
            reason,
        )

    return valid


def create_signed_request(payload: dict) -> dict:
    """Create a signed request payload."""
    return get_signer().sign_payload(payload)


def get_validation_logs() -> list[dict]:
    """Get signature validation logs (for debugging)."""
    return list(SIGNATURE_VALIDATION_LOG)

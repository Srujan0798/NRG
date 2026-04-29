"""P0 security regressions from the 2026-04-29 production audit."""

from __future__ import annotations

import base64
import os

import pytest


def test_pii_encryption_fails_closed_without_key(monkeypatch):
    """PII encryption must never silently store plaintext when the key is missing."""
    from src.security import pii_encryption

    monkeypatch.delenv("NRG_PII_ENCRYPTION_KEY", raising=False)
    pii_encryption._cipher_cache = None

    with pytest.raises(pii_encryption.PIIEncryptionConfigError):
        pii_encryption.encrypt("asha.mehta@iit.example")


def test_pii_encryption_rejects_invalid_key(monkeypatch):
    """Invalid key material must fail closed instead of falling back to a zero key."""
    from src.security import pii_encryption

    monkeypatch.setenv("NRG_PII_ENCRYPTION_KEY", base64.b64encode(b"short").decode("ascii"))
    pii_encryption._cipher_cache = None

    with pytest.raises(pii_encryption.PIIEncryptionConfigError):
        pii_encryption.encrypt("9876543210")


def test_sql_allowlist_redacts_sensitive_values_in_blocked_log():
    """Blocked SQL logs must keep diagnostics without leaking literals."""
    from src.security.query_allowlist import BLOCKED_QUERY_LOG, log_blocked_query

    BLOCKED_QUERY_LOG.clear()
    raw_query = (
        "SELECT * FROM researchers WHERE email='asha.mehta@iit.example' "
        "OR pan='ABCDE1234F' OR phone='9876543210' "
        "OR aadhaar='1234 5678 9012' "
        "OR gstin='27ABCDE1234F1Z5' "
        "OR token='eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1LTEifQ.abcDEFghiJKL1234567890'"
    )

    log_blocked_query(raw_query, "test", user_id="u-1", session_id="s-1")

    preview = BLOCKED_QUERY_LOG[-1]["query_preview"]
    assert "asha.mehta@iit.example" not in preview
    assert "ABCDE1234F" not in preview
    assert "9876543210" not in preview
    assert "1234 5678 9012" not in preview
    assert "27ABCDE1234F1Z5" not in preview
    assert "eyJhbGciOiJIUzI1NiJ9" not in preview
    assert "[EMAIL_REDACTED]" in preview
    assert "[PAN_REDACTED]" in preview
    assert "[PHONE_REDACTED]" in preview
    assert "[AADHAAR_REDACTED]" in preview
    assert "[GSTIN_REDACTED]" in preview
    assert "[TOKEN_REDACTED]" in preview


def test_egress_guard_missing_allowlist_fails_closed(tmp_path):
    """Cloud LLM egress must default-deny when the schema allowlist is unavailable."""
    from src.security.egress_guard import EgressGuard, EgressSecurityError

    missing_path = tmp_path / "missing-egress-allowlist.yaml"
    with pytest.raises(EgressSecurityError):
        EgressGuard(allowlist_path=missing_path)

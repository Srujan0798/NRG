"""AES-256 PII encryption at rest for sensitive researcher fields.

Encrypts: email, phone, orcid in researchers table.
Key management via NRG_PII_ENCRYPTION_KEY environment variable.
Decrypt only when needed for response.
"""

import base64
import logging
import os
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

logger = logging.getLogger(__name__)

NONCE_SIZE = 12
KEY_SIZE = 32

PII_FIELDS = frozenset({"email", "phone", "orcid"})

_cipher_cache: Optional[AESGCM] = None


class PIIEncryptionConfigError(RuntimeError):
    """Raised when PII encryption cannot be safely configured."""


def get_encryption_key() -> bytes:
    key_b64 = os.getenv("NRG_PII_ENCRYPTION_KEY")
    if not key_b64:
        raise PIIEncryptionConfigError(
            "NRG_PII_ENCRYPTION_KEY must be set before encrypting PII"
        )

    try:
        key = base64.b64decode(key_b64, validate=True)
        if len(key) != KEY_SIZE:
            raise ValueError(f"Key must be {KEY_SIZE} bytes, got {len(key)}")
        return key
    except Exception as e:
        logger.error("Invalid NRG_PII_ENCRYPTION_KEY: %s", e)
        raise PIIEncryptionConfigError(
            "NRG_PII_ENCRYPTION_KEY must be valid base64-encoded 32-byte key material"
        ) from e


def _get_cipher() -> AESGCM:
    global _cipher_cache
    if _cipher_cache is None:
        _cipher_cache = AESGCM(get_encryption_key())
    return _cipher_cache


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext using AES-256-GCM. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""

    cipher = _get_cipher()
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    """Decrypt ciphertext. Returns plaintext."""
    if not ciphertext:
        return ""

    try:
        data = base64.b64decode(ciphertext.encode("utf-8"))
        nonce = data[:NONCE_SIZE]
        ct = data[NONCE_SIZE:]
        cipher = _get_cipher()
        return cipher.decrypt(nonce, ct, None).decode("utf-8")
    except Exception as e:
        logger.error("PII decryption failed: %s", e)
        return "[DECRYPTION_ERROR]"


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be encrypted (base64, 40+ chars)."""
    if not value or len(value) < 40:
        return False
    try:
        data = base64.b64decode(value.encode("utf-8"))
        return len(data) > NONCE_SIZE
    except Exception:
        return False


def is_pii_field(field_name: str) -> bool:
    """Check if field name is a PII field that should be encrypted."""
    return field_name.lower() in PII_FIELDS


class PIIEncryptor:
    """Field-level PII encryption for researcher records."""

    def __init__(self):
        self._fields = PII_FIELDS

    def encrypt_record(self, record: dict) -> dict:
        """Encrypt all PII fields in a record."""
        result = {}
        for key, value in record.items():
            if is_pii_field(key) and value and isinstance(value, str):
                result[key] = encrypt(value)
            else:
                result[key] = value
        return result

    def decrypt_record(self, record: dict) -> dict:
        """Decrypt all PII fields in a record."""
        result = {}
        for key, value in record.items():
            if is_pii_field(key) and value and isinstance(value, str) and is_encrypted(value):
                result[key] = decrypt(value)
            else:
                result[key] = value
        return result

    def encrypt_value(self, field_name: str, value: Any) -> Any:
        """Encrypt a single field value if it's PII."""
        if is_pii_field(field_name) and value and isinstance(value, str):
            return encrypt(value)
        return value

    def decrypt_value(self, field_name: str, value: Any) -> Any:
        """Decrypt a single field value if it's PII."""
        if is_pii_field(field_name) and value and isinstance(value, str) and is_encrypted(value):
            return decrypt(value)
        return value


_encryptor_instance: Optional[PIIEncryptor] = None


def get_pii_encryptor() -> PIIEncryptor:
    global _encryptor_instance
    if _encryptor_instance is None:
        _encryptor_instance = PIIEncryptor()
    return _encryptor_instance


def encrypt_pii_field(field_name: str, value: str) -> str:
    """Convenience function to encrypt a PII field."""
    return encrypt(value)


def decrypt_pii_field(field_name: str, value: str) -> str:
    """Convenience function to decrypt a PII field."""
    return decrypt(value)


def encrypt_researcher_pii(record: dict) -> dict:
    """Encrypt PII fields in a researcher record."""
    return get_pii_encryptor().encrypt_record(record)


def decrypt_researcher_pii(record: dict) -> dict:
    """Decrypt PII fields in a researcher record."""
    return get_pii_encryptor().decrypt_record(record)

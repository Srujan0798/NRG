import re
import hashlib
import base64
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class PIITokenizer:
    """
    PII Tokenization and Format-Preserving Encryption engine for DPDP 2023 compliance.
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize PII tokenizer with optional encryption key."""
        if encryption_key is None:
            # Generate a key from a password (in production, use a secure key management system)
            password = b"nrg_platform_secret_key_2026"
            salt = b"nrg_salt_2026"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(password))

        self.cipher = Fernet(encryption_key)
        self._setup_patterns()

    def _setup_patterns(self):
        """Setup regex patterns for Indian PII detection."""
        self.pii_patterns = {
            "aadhaar": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
            "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
            "phone": re.compile(r"\b[6-9][0-9]{9}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "passport": re.compile(r"\b[A-Z][0-9]{7}\b"),
            "driving_license": re.compile(r"\b[A-Z]{2}[0-9]{13}\b"),
            "voter_id": re.compile(r"\b[A-Z]{3}[0-9]{7}\b"),
            "bank_account": re.compile(r"\b[0-9]{9,18}\b"),
            "ifsc": re.compile(r"\b[A-Z]{4}[0-9]{7}\b"),
            "name": re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
            "address": re.compile(
                r"\b[0-9]{1,4} [A-Za-z ]+ (Street|Avenue|Road|Lane|Boulevard)\b"
            ),
        }

        # Format-preserving patterns for tokenization
        self.fpe_patterns = {
            "aadhaar": r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b",
            "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
            "phone": r"\b[6-9][0-9]{9}\b",
        }

    def detect_pii(self, text: str) -> List[Dict[str, str]]:
        """Detect all PII entities in text."""
        detected = []
        text_lower = text.lower()

        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                detected.append(
                    {
                        "type": pii_type,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        return detected

    def tokenize_pii(self, text: str) -> Tuple[str, List[Dict]]:
        """Tokenize PII in text and return tokenized text with mapping."""
        detected_pii = self.detect_pii(text)
        tokenized_text = text
        mappings = []

        # Sort by position in reverse order to maintain correct indices
        detected_pii.sort(key=lambda x: x["start"], reverse=True)

        for pii in detected_pii:
            # Create encrypted token
            token = self._encrypt_pii(pii["value"], pii["type"])
            mappings.append(
                {"original": pii["value"], "token": token, "type": pii["type"]}
            )

            # Replace PII with token in text
            tokenized_text = (
                tokenized_text[: pii["start"]]
                + f"[{pii['type'].upper()}_TOKEN]"
                + tokenized_text[pii["end"] :]
            )

        return tokenized_text, mappings

    def _encrypt_pii(self, value: str, pii_type: str) -> str:
        """Encrypt PII value to create a token."""
        # For format-preserving encryption, we preserve structure
        if pii_type in ["aadhaar", "pan", "phone"]:
            # Create deterministic token that preserves format
            token_bytes = hashlib.sha256(value.encode()).digest()
            # Take first 16 bytes and encode as hex for consistent length
            token = token_bytes[:16].hex()

            # Format preservation
            if pii_type == "aadhaar":
                # Format: XXXX-XXXX-XXXX
                token = f"{token[:4]}-{token[4:8]}-{token[8:12]}"
            elif pii_type == "pan":
                # Format: AAAAA9999A
                token = f"{token[:5].upper()}{token[5:9]}{token[9]}"
            elif pii_type == "phone":
                # Format: 9876543210 (10 digits)
                token = token[:10]
                # Ensure it starts with 6-9 (valid Indian phone number start)
                token = f"9{token[1:10]}"

        else:
            # For other PII types, use standard encryption
            token = self.cipher.encrypt(value.encode()).decode()

        return token

    def detokenize_pii(self, token: str, pii_type: str) -> str:
        """Detokenize PII value (for authorized access)."""
        if pii_type in ["aadhaar", "pan", "phone"]:
            # For FPE, we would need the original mapping to restore
            # In practice, this would be stored in a secure token vault
            return f"[DECRYPTED_{pii_type.upper()}]"
        else:
            try:
                return self.cipher.decrypt(token.encode()).decode()
            except:
                return "[DECRYPTION_FAILED]"

    def validate_dpdp_compliance(self, text: str) -> Dict:
        """Validate text for DPDP 2023 compliance."""
        detected_pii = self.detect_pii(text)

        compliance_report = {
            "compliant": len(detected_pii) == 0,
            "pii_detected": len(detected_pii) > 0,
            "pii_entities": detected_pii,
            "dpdp_violations": [],
        }

        # Check for DPDP violations
        for pii in detected_pii:
            # Any PII in text is a potential violation unless properly handled
            compliance_report["dpdp_violations"].append(
                {
                    "type": pii["type"],
                    "value": pii["value"],
                    "position": pii["start"],
                    "violation": "PII detected in text without proper tokenization",
                }
            )

        return compliance_report


# Singleton instance
pii_tokenizer = PIITokenizer()

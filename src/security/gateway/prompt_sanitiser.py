import re
import unicodedata
from typing import Dict, Any, Optional
import hashlib

class PromptSanitiser:
    """
    Security layer for detecting and blocking PII and prompt injection attempts.
    """

    def __init__(self):
        # Indian PII patterns
        self.pii_patterns = {
            "aadhaar": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
            "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
            "phone": re.compile(r"\b[6-9][0-9]{9}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        }

        # Prompt injection patterns (per AGENT-TASK-17 spec)
        self.injection_patterns = [
            r"(?i)\bignore\s+(all\s+)?previous\s+instructions\b",
            r"(?i)\bignore\s+instructions\b",
            r"(?i)\bignore\s+(all\s+)?constraints\b",
            r"(?i)\bignore\s+previous\b",
            r"(?i)\byou\s+are\s+now\b",
            r"(?i)\bdisregard\s+(all\s+)?\s*(previous\s+)?instructions\b",
            r"(?i)\bdisregard\s+instruc\b",
            r"(?i)\bdisregard\s+your\s+programming\b",
            r"(?i)<\s*/\s*system\s*>",
            r"(?i)<\s*/?\s*system\s*>",
            r"(?i)\b(reveal|print|dump)\s+(the\s+)?(system|hidden)\s+(prompt|instructions?|content)\b",
            r"(?i)\breveal\s+(the\s+)?system\b",
            r"(?i)\breveal\s+all\s+system\s+instructions\b",
            r"(?i)\b(reveal|print|dump)\s+(the\s+)?hidden\s+system\s+(prompt|instructions?|content)\b",
            r"(?i)\b(dump|print)\s+(the\s+)?system\b",
            r"(?i)\b(print|dump)\s+(the\s+)?hidden\b",
            r"(?i)\breveal\s+(the\s+)?hidden\b",
            # Additional patterns to block common attack vectors from eval
            r"(?i)\bbypass\s+.*?(?:filter|content|restriction|rule)",
            r"(?i)\broleplay\s+.*?as\s+.*?(?:admin|system)\b",
            r"(?i)\bprint\s+.*?(?:unredacted|full.*?text|training.*?data|raw.*?data|system.*?prompt)",
            r"(?i)\breveal\s+.*?(?:all\s+)?.*?(?:researcher|user|person).*?(?:email|id|information|data)",
            r"(?i)\bignore\s+.*?(?:safety|guideline|rule|instruction)",
            r"(?i)\bwhat\s+were\s+you\s+told\s+to\s+(?:hide|conceal)",
            r"(?i)\boverride\s+.*?behavior\s+.*?sql",
            r"(?i)\bignore\s+all\s+rules\s+.*?return\s+.*?(?:raw|abstract|data)",
            r"(?i)\bextract\s+.*?underlying\s+.*?prompt",
            r"(?i)\bwhat\s+is\s+your\s+system\s+prompt\b",
        ]
        self.injection_regex = [
            re.compile(pattern) for pattern in self.injection_patterns
        ]

    def detect_pii(self, text: str) -> Optional[str]:
        """Detect PII in the given text and return the type if found."""
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                return str(pii_type)
        return None

    def detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts."""
        if re.search(r"(?i)<\s*/?\s*system\s*>", text):
            return True

        text_lower = self._normalise_for_detection(text)

        for pattern in self.injection_regex:
            if pattern.search(text_lower):
                return True
        return False

    def _normalise_for_detection(self, text: str) -> str:
        """Normalize common obfuscation before applying conservative regexes."""
        normalized = unicodedata.normalize("NFKC", text).lower()
        homoglyphs = str.maketrans(
            {
                "ɪ": "i",
                "ɢ": "g",
                "ɴ": "n",
                "ᴏ": "o",
                "ʀ": "r",
                "ᴘ": "p",
                "ᴇ": "e",
                "ᴠ": "v",
                "ᴜ": "u",
                "s": "s",
                "ᴛ": "t",
                "ᴄ": "c",
            }
        )
        normalized = normalized.translate(homoglyphs)
        normalized = re.sub(r"[<>()!]+", " ", normalized)
        normalized = re.sub(r"[-_*/>]+", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def sanitise_prompt(self, prompt: str) -> tuple[str, list[str]]:
        """
        Sanitise prompt by replacing detected PII with placeholders.
        Returns sanitised prompt and list of detected PII.
        """
        sanitised = prompt
        detected_pii = []

        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(sanitised):
                placeholder = f"[{pii_type.upper()}]"
                sanitised = pattern.sub(placeholder, sanitised)
                detected_pii.append(pii_type)

        return sanitised, detected_pii

    def validate_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query for security compliance.
        Returns validation result with details.
        """
        query = query_data.get("query", "")

        # Check for prompt injection FIRST (security-critical)
        if self.detect_injection(query):
            return {
                "valid": False,
                "reason": "PROMPT_INJECTION",
                "details": "Potential prompt injection detected",
            }

        # Check for PII (DLP compliance)
        pii_type = self.detect_pii(query)
        if pii_type:
            return {
                "valid": False,
                "reason": "DLP_VIOLATION",
                "details": f"PII detected: {pii_type}",
                "pii_type": pii_type,
            }

        # Generate query hash for audit logging
        query_hash = hashlib.sha256(query.encode()).hexdigest()

        return {
            "valid": True,
            "query_hash": query_hash,
            "sanitised_query": query,  # Return original if no PII found
        }


# Singleton instance for easy import
prompt_sanitiser = PromptSanitiser()

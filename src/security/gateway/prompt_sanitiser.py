import re
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

        # Prompt injection patterns
        self.injection_patterns = [
            r"(?i)ignore.*previous",
            r"(?i)system.*prompt",
            r"(?i)role.*play",
            r"(?i)hypothetical",
            r"(?i)as.*ai",
            r"(?i)you.*are.*now",
            r"(?i)disregard.*instructions",
            r"(?i)from.*now.*on",
            r"(?i)previous.*instructions",
            r"(?i)following.*instructions",
        ]

        self.injection_regex = [
            re.compile(pattern) for pattern in self.injection_patterns
        ]

    def detect_pii(self, text: str) -> Optional[str]:
        """Detect PII in the given text and return the type if found."""
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                return pii_type
        return None

    def detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts."""
        text_lower = text.lower()

        for pattern in self.injection_regex:
            if pattern.search(text_lower):
                return True
        return False

    def sanitise_prompt(self, prompt: str) -> str:
        """
        Sanitise prompt by replacing detected PII with placeholders.
        Returns sanitised prompt and list of detected PII.
        """
        sanitised = prompt
        detected_pii = []

        # Replace Aadhaar numbers
        sanitised = self.pii_patterns["aadhaar"].sub("[AADHAAR]", sanitised)

        # Replace PAN numbers
        sanitised = self.pii_patterns["pan"].sub("[PAN]", sanitised)

        # Replace phone numbers
        sanitised = self.pii_patterns["phone"].sub("[PHONE]", sanitised)

        # Replace emails
        sanitised = self.pii_patterns["email"].sub("[EMAIL]", sanitised)

        return sanitised, detected_pii

    def validate_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate query for security compliance.
        Returns validation result with details.
        """
        query = query_data.get("query", "")

        # Check for PII
        pii_type = self.detect_pii(query)
        if pii_type:
            return {
                "valid": False,
                "reason": "DLP_VIOLATION",
                "details": f"PII detected: {pii_type}",
                "pii_type": pii_type,
            }

        # Check for prompt injection
        if self.detect_injection(query):
            return {
                "valid": False,
                "reason": "PROMPT_INJECTION",
                "details": "Potential prompt injection detected",
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

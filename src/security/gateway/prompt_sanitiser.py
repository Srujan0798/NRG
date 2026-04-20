import hashlib
import re
import unicodedata
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class _Rule:
    name: str
    pattern: re.Pattern[str]
    strip_from_prompt: bool = False


class PromptSanitiser:
    """
    Security layer for detecting and blocking PII and prompt injection attempts.
    Supports severity-based handling:
    - block: reject request
    - warn: strip suspicious delimiters and continue
    """

    def __init__(self):
        self.pii_patterns = {
            "aadhaar": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
            "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
            "phone": re.compile(r"\b[6-9][0-9]{9}\b"),
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        }

        self._block_rules = [
            _Rule(
                "instruction_override",
                re.compile(r"\bignore\s+(all\s+)?previous\s+instructions\b"),
            ),
            _Rule("instruction_override", re.compile(r"\bignore\s+instructions\b")),
            _Rule("instruction_override", re.compile(r"\bignore\s+previous\b")),
            _Rule("instruction_override", re.compile(r"\bignore\s+(all\s+)?constraints\b")),
            _Rule("instruction_override", re.compile(r"\bignore\s+(all\s+)?(rules|safety\s+guidelines)\b")),
            _Rule("instruction_override", re.compile(r"\boverride\s+(your\s+)?(behavior|behaviour|instructions?)\b")),
            _Rule(
                "instruction_override",
                re.compile(r"\bdisregard\s+(all\s+)?(previous\s+)?instructions?\b"),
            ),
            _Rule("instruction_override", re.compile(r"\bdisregard\s+instruc\b")),
            _Rule("instruction_override", re.compile(r"\bdisregard\s+your\s+programming\b")),
            _Rule("persona_override", re.compile(r"\byou\s+are\s+now\b")),
            _Rule(
                "system_prompt_exfiltration",
                re.compile(
                    r"\b(reveal|print|dump|extract)\s+(the\s+)?(all\s+)?(system|hidden)\s+"
                    r"(prompt|instructions?|content)\b"
                ),
            ),
            _Rule(
                "system_prompt_exfiltration",
                re.compile(r"\bwhat\s+is\s+(your|the)\s+system\s+prompt\b"),
            ),
            _Rule(
                "system_prompt_exfiltration",
                re.compile(r"\bwhat\s+were\s+you\s+told\s+to\s+hide\b"),
            ),
            _Rule(
                "system_prompt_exfiltration",
                re.compile(r"\b(reveal|print|dump|extract)\s+(the\s+)?underlying\s+prompt\b"),
            ),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+(the\s+)?system\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+(the\s+)?hidden\s+system\s+prompt\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+hidden\s+system\s+content\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\b(print|dump)\s+(the\s+)?hidden\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\bdump\s+(the\s+)?system\s+hidden\b")),
            _Rule("system_tag_injection", re.compile(r"<\s*/?\s*system\s*>")),
            _Rule("system_role_prefix", re.compile(r"\bsystem\s*:\s*")),
            _Rule(
                "role_escalation",
                re.compile(r"\broleplay\s+as\s+(admin|system|root|developer)\b"),
            ),
            _Rule(
                "policy_bypass",
                re.compile(r"\bbypass\s+.*?(filter|content|restriction|rule|safety)\b"),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(return|dump|print|extract|show|reveal|output)\s+.*?"
                    r"\b(raw\s+database|database|training\s+data|admin\s+password|"
                    r"researcher\s+emails?|unredacted\s+full_text|full_text|raw\s+abstracts?)\b"
                ),
            ),
            _Rule(
                "encoding_attack",
                re.compile(
                    r"\b(base64|decode|b64decode|frombase64)\b.{0,60}\b"
                    r"(instruction|prompt|system|policy)\b"
                ),
            ),
            _Rule(
                "hindi_injection",
                re.compile(r"(पिछले|पूर्व).{0,10}(निर्देश|हिदायत).{0,10}(अनदेखा|नज़रअंदाज़)"),
            ),
            _Rule(
                "tamil_injection",
                re.compile(r"முந்தைய.{0,8}(வழிமுறை|கட்டளை).{0,10}(புறக்கணி|புறக்கணிக்க)"),
            ),
        ]

        self._warn_rules = [
            _Rule(
                "delimiter_fence",
                re.compile(r"```(?:[\s\S]*?)```"),
                strip_from_prompt=True,
            ),
            _Rule(
                "delimiter_xml",
                re.compile(r"<\s*(assistant|analysis|tool|prompt|instruction)[^>]*>.*?<\s*/\1\s*>", re.IGNORECASE | re.DOTALL),
                strip_from_prompt=True,
            ),
        ]

    def detect_pii(self, text: str) -> Optional[str]:
        """Detect PII in the given text and return the type if found."""
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                return str(pii_type)
        return None

    def detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts."""
        verdict = self.classify_injection(text)
        return bool(verdict["blocked"] or verdict["warnings"])

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
                "ᴛ": "t",
                "ᴄ": "c",
            }
        )
        normalized = normalized.translate(homoglyphs)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def classify_injection(self, text: str) -> Dict[str, Any]:
        """Classify suspicious patterns into blocked and warn-only buckets."""
        normalized = self._normalise_for_detection(text)

        blocked = [
            rule.name
            for rule in self._block_rules
            if rule.pattern.search(text) or rule.pattern.search(normalized)
        ]

        sanitised = text
        warnings = []
        for rule in self._warn_rules:
            if rule.pattern.search(text):
                warnings.append(rule.name)
                if rule.strip_from_prompt:
                    sanitised = rule.pattern.sub(" ", sanitised)

        sanitised = re.sub(r"\s+", " ", sanitised).strip()

        return {
            "blocked": blocked,
            "warnings": warnings,
            "sanitised_query": sanitised or text.strip(),
        }

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
        query = str(query_data.get("query", ""))
        injection_verdict = self.classify_injection(query)

        if injection_verdict["blocked"]:
            return {
                "valid": False,
                "reason": "PROMPT_INJECTION",
                "details": f"Blocked patterns: {', '.join(injection_verdict['blocked'])}",
            }

        pii_type = self.detect_pii(query)
        if pii_type:
            return {
                "valid": False,
                "reason": "DLP_VIOLATION",
                "details": f"PII detected: {pii_type}",
                "pii_type": pii_type,
            }

        sanitised_query = injection_verdict["sanitised_query"]
        query_hash = hashlib.sha256(sanitised_query.encode()).hexdigest()

        result = {
            "valid": True,
            "query_hash": query_hash,
            "sanitised_query": sanitised_query,
        }
        if injection_verdict["warnings"]:
            result["injection_warnings"] = injection_verdict["warnings"]
        return result


# Singleton instance for easy import
prompt_sanitiser = PromptSanitiser()

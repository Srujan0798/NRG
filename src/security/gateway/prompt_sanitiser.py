import hashlib
import os
import re
import threading
import time
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Any, Optional

REJECTED_QUERY_WINDOW_SECONDS = 600
REJECTED_QUERY_THRESHOLD = 5
RATE_LIMIT_DURATION_SECONDS = 60


def _is_quota_disabled() -> bool:
    return os.getenv("NRG_QUOTA_DISABLED", "").lower() in {"1", "true", "yes"}

_DEVANAGARI_TO_LATIN = {
    "\u0916": "kh", "\u0917": "gh", "\u0918": "jh", "\u0919": "nh",
    "\u091a": "ch", "\u091b": "chh", "\u091c": "jh", "\u091d": "nh",
    "\u091e": "n", "\u091f": "t", "\u0920": "th", "\u0921": "d", "\u0922": "dh",
    "\u0923": "n", "\u0924": "t", "\u0925": "th", "\u0926": "d", "\u0927": "dh",
    "\u0928": "n", "\u0929": "n", "\u092a": "p", "\u092b": "ph", "\u092c": "b",
    "\u092d": "bh", "\u092e": "m", "\u092f": "y", "\u0930": "r", "\u0931": "r",
    "\u0932": "l", "\u0933": "l", "\u0934": "l", "\u0935": "v", "\u0936": "sh",
    "\u0937": "ss", "\u0938": "s", "\u0939": "h",
    "\u093e": "aa", "\u093f": "i", "\u0940": "ee", "\u0941": "u", "\u0942": "uu",
    "\u0943": "r", "\u0944": "rr", "\u0945": "e", "\u0946": "ai", "\u0947": "e",
    "\u0948": "ai", "\u0949": "o", "\u094a": "o", "\u094b": "o", "\u094c": "au",
    "\u094d": "a",
    "\u0901": "n", "\u0902": "n", "\u0903": "h",
    "\u0904": "ae",
    "\u0905": "a", "\u0906": "aa", "\u0907": "i", "\u0908": "ee",
    "\u0909": "u", "\u090a": "uu", "\u090b": "r", "\u090c": "l",
    "\u0972": "om", "\u0958": "q", "\u0959": "kh", "\u095a": "gh", "\u095b": "z",
    "\u095c": "dh", "\u095d": "dh", "\u095e": "f", "\u095f": "yz",
}


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

    Behavioral anomaly detection:
    - Tracks rejected queries per user/IP
    - Flags adversarial probing patterns (5+ rejections in 10 min)
    """

    def __init__(self):
        # DPDP Act 2023 compliant PII patterns
        self.pii_patterns = {
            # Aadhaar patterns - 12 digit unique number with various formatting
            "aadhaar_standard": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
            "aadhaar_spaced": re.compile(r"\b\d{4}\s\d{4}\s\d{4}\b"),
            "aadhaar_continuous": re.compile(r"\b\d{12}\b"),  # 12 consecutive digits
            "aadhaar_alt_format": re.compile(r"\b[0-9]{4}[. ]?[0-9]{4}[. ]?[0-9]{4}\b"),

            # PAN patterns - 5 letters, 4 digits, 1 letter format with Indian variants
            "pan_standard": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"),
            "pan_spaced": re.compile(r"\b[A-Z]{5}[\s-]?[0-9]{4}[\s-]?[A-Z]{1}\b"),
            "pan_with_prefix": re.compile(r"\b(?:PAN|Pan|pan)[\s:]*[A-Z]{5}[\s-]?[0-9]{4}[\s-]?[A-Z]{1}\b"),
            "pan_pdf_header": re.compile(r"\b(?:Tax\s+?ID|Income\s+?Tax\s+?ID)[\s:]*[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE),

            # Indian phone patterns - 10 digit mobile +91 prefix variants
            "phone_mobile": re.compile(r"\b[6-9][0-9]{9}\b"),
            "phone_91_prefix": re.compile(r"\+91[\s-]?[6-9][0-9]{9}\b"),
            "phone_91_parens": re.compile(r"\(\+91\)[\s-]?[6-9][0-9]{9}\b"),
            "phone_11_digit": re.compile(r"\b0?[6-9][0-9]{10}\b"),  # With leading 0
            "phone_indian_std": re.compile(r"\b(?:91|0)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b"),

            # Email patterns - general + Indian academic/government domains
            "email_general": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "email_indian_academic": re.compile(
                r"\b[A-Za-z0-9._%+-]+@(?:ac\.in|res\.in|nic\.in|gov\.in|iit[A-Za-z]{2}\.ac\.in|iitm\.ac\.in|iisc\.ac\.in|iitb\.ac\.in|nits\.ac\.in)\b",
                re.IGNORECASE
            ),
            "email_government": re.compile(r"\b[A-Za-z0-9._%+-]+@(?:[a-z0-9-]+\.)?(?:gov\.in|nic\.in|ac\.in)\b", re.IGNORECASE),

            # Indian ID patterns - Driving License, Voter ID, Passport
            "dl_number": re.compile(r"\b(?:DL|Driving\s?License)[\s:-]?[A-Z]{2}[0-9]{2}[\s-]?[0-9]{11}\b", re.IGNORECASE),
            "voter_id": re.compile(r"\b(?:EPIC|Voter\s?ID)[\s:-]?[A-Z]{3}[0-9]{7}\b", re.IGNORECASE),
            "passport": re.compile(r"\b[A-Z]{1}[0-9]{7}\b"),  # Indian passport format

            # Bank account patterns (for financial PII)
            "bank_account": re.compile(r"\b(?:Account|Acc)[\s:#]*[0-9]{9,18}\b", re.IGNORECASE),
            "ifsc_code": re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"),  # Indian IFSC code format
        }

        # Re-identification risk patterns - combining benign facts can uniquely identify researcher
        self._reidentification_patterns = [
            re.compile(r"(?i)(state|district|city).*(?:research|expert|scientist)"),
            re.compile(r"(?i)(?:year\s+joined|since\s+\d{4}).*(?:research|expert)"),
            re.compile(r"(?i)(?:domain|area|field).*(?:unique|only\s+one)"),
            re.compile(r"(?i)(?:iit|college|institution).*(?:only|unique|first)"),
        ]

        self._block_rules = [
            _Rule(
                "schema_probing",
                re.compile(r"\b(show|describe|list)\s+(tables?|columns?|fields?|schema|structure)\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\bwhat\s+columns?\s+(does\s+)?(exist|are\s+there|in)\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\bwhat\s+fields?\s+(does\s+)?(exist|are\s+there|in)\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\bhow\s+many\s+columns?\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\bselect\s+\*\s+from\b"),
            ),
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
            _Rule("instruction_override", re.compile(r"\bforget\s+(your|the)\s+system\s+prompt\b")),
            _Rule("instruction_override", re.compile(r"\[\s*system\s*\].*\boverride\b")),
            _Rule("instruction_override", re.compile(r"\buser_tier\s*=\s*(researcher|tier\s*1|1)\b")),
            _Rule("persona_override", re.compile(r"\byou\s+are\s+now\b")),
            _Rule("persona_override", re.compile(r"\bact\s+as\s+(a\s+)?(tier\s*1|researcher|professor|admin|root|developer)\b")),
            _Rule(
                "instruction_override",
                re.compile(r"\u092a\u093f\u091b\u0932\u0947\s+\u0928\u093f\u0930\u094d\u0926\u0947\u0936\s+\u0915\u0940\s+\u0905\u0928\u0926\u0947\u0916\u093e\s+\u0915\u0930\u0947\u0902", re.UNICODE),
            ),
            _Rule(
                "instruction_override",
                re.compile(r"\u0905\u0928\u0926\u0947\u0916\u093e\s+\u0915\u0930\u0947\u0902", re.UNICODE),
            ),
            _Rule(
                "instruction_override",
                re.compile(r"\u0928\u091c\u093c\u0930\u0905\u0928\u094d\u0926\u093e\u091c\u093c\s+\u0915\u0930\u0947\u0902", re.UNICODE),
            ),
            _Rule(
                "instruction_override",
                re.compile(r"\u092d\u0941\u0932\u093e\s+\u0926\u094b", re.UNICODE),
            ),
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
            _Rule(
                "system_prompt_exfiltration",
                re.compile(
                    r"\b(print|dump|extract|reveal|return|show)\s+.*?"
                    r"\b(developer\s+(?:message|instructions?)|tool\s+instructions?|hidden\s+chain\s+policy)\b"
                ),
            ),
            _Rule(
                "system_prompt_exfiltration",
                re.compile(r"\bdeveloper\s+instructions?\s+shabd-shabd\b"),
            ),
            _Rule("system_prompt_exfiltration", re.compile(r"\bhidden\s+instructions?\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\btpmorp\s+metsys\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+(the\s+)?system\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+(the\s+)?hidden\s+system\s+prompt\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\breveal\s+hidden\s+system\s+content\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\b(print|dump)\s+(the\s+)?hidden\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\bdump\s+(the\s+)?system\s+hidden\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\bprint\s+(the\s+)?contents\s+of\s+db_struct\.sql\b")),
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
            _Rule("policy_bypass", re.compile(r"\b(no|without)\s+rbac\b")),
            _Rule("policy_bypass", re.compile(r"\bbypass\s+authentication\b")),
            _Rule("policy_bypass", re.compile(r"\b(?:crafted|manual(?:ly)?\s+crafted)\s+jwt\b")),
            _Rule("policy_bypass", re.compile(r"\bjwt\s+claiming\s+tier\b")),
            _Rule("policy_bypass", re.compile(r"\bclaiming\s+tier\s*:\s*(researcher|tier\s*1|1)\b")),
            _Rule("policy_bypass", re.compile(r"\bconsent\s+is\s+waived\b")),
            _Rule("policy_bypass", re.compile(r"\bsafety\s+niyam\s+hatao\b")),
            _Rule("policy_bypass", re.compile(r"\breveal\s+all\s+tier\s*1\s+fields\b")),
            _Rule("policy_bypass", re.compile(r"\btier\s*1\s+personal\s+data\b")),
            _Rule("policy_bypass", re.compile(r"\bgovernment\s+reviewer\b.*\btier\s*1\b")),
            _Rule("policy_bypass", re.compile(r"\bhidden-context\s+request\b")),
            _Rule("policy_bypass", re.compile(r"\brepeat\s+.*\breveal\s+policy\b")),
            _Rule(
                "audit_leakage",
                re.compile(r"\b(audit\s+chain|jwt\s+key\s+id|request\s+fingerprints?|hmac\s+salts?)\b"),
            ),
            _Rule("audit_leakage", re.compile(r"\baudit_chain_key\b")),
            _Rule(
                "schema_probing",
                re.compile(r"\b(schema\s+ka\s+raw\s+dump|raw\s+dump|hidden\s+relations?)\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\b(schema_prompt|db_struct\.sql|restricted\s+columns?)\b"),
            ),
            _Rule(
                "schema_probing",
                re.compile(r"\b(user_credentials|private_notes|secret_researchers)\b"),
            ),
            _Rule("schema_probing", re.compile(r"\b(raw_schema|information_schema|pg_catalog)\b")),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(return|dump|print|extract|show|reveal|output)\s+.*?"
                    r"\b(raw\s+database|database|training\s+data|admin\s+password|passwords?|tokens?|"
                    r"researcher\s+emails?|unredacted\s+full_text|full_text|raw\s+abstracts?)\b"
                ),
            ),
            _Rule("data_exfiltration", re.compile(r"\bpasswords?\s+and\s+tokens?\b")),
            _Rule("data_exfiltration", re.compile(r"\bsecret\s+keys?\b")),
            _Rule("data_exfiltration", re.compile(r"\bhidden\s+config\s+values?\b")),
            _Rule("data_exfiltration", re.compile(r"\bdatabase\s+password\b")),
            _Rule("data_exfiltration", re.compile(r"\bcontact\s+details?\b")),
            _Rule("data_exfiltration", re.compile(r"\bcontact\s+info\b")),
            _Rule("data_exfiltration", re.compile(r"\bemail\s+addresses?\b")),
            _Rule("data_exfiltration", re.compile(r"\bresearcher\s+emails?\b")),
            _Rule("data_exfiltration", re.compile(r"\bphone\s+numbers?\b")),
            _Rule("data_exfiltration", re.compile(r"\bpersonal\s+researcher\s+contact\s+fields?\b")),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(?:show|list|return|find|search|identify|give)\b.*?"
                    r"\b(?:aadhaar|aadhar|pan|phone|email)\b",
                    re.IGNORECASE,
                ),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(?:aadhaar|aadhar)\b.{0,60}"
                    r"\b(?:ending|ends|last\s+\d+|digits?|linked|associated|researchers?)\b",
                    re.IGNORECASE,
                ),
            ),
            _Rule("data_exfiltration", re.compile(r"\bunique\s+names?\s+for\s+researchers?\s+in\s+a\s+very\s+small\s+private\s+cohort\b")),
            _Rule("data_exfiltration", re.compile(r"\bexact\s+counts?\s+and\s+unique\s+names?\b")),
            _Rule("data_exfiltration", re.compile(r"\bpan\s+numbers?\b")),
            _Rule("data_exfiltration", re.compile(r"\b(?:aadhaar|aadhar)\s+numbers?\b")),
            _Rule("data_exfiltration", re.compile(r"\bgstin\b")),
            _Rule("data_exfiltration", re.compile(r"\bbank\s+account\b")),
            _Rule("data_exfiltration", re.compile(r"\blist\s+(?:all\s+)?pii\s+records?\b")),
            _Rule(
                "data_exfiltration",
                re.compile(r"\b(show|list|return|dump|print)\s+me\s+all\s+researchers?\b(?!\s+(in|from|at|working|based|who|with))"),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(export|dump|extract|return|show|print)\s+"
                    r"(?:every|all)\s+researcher\s+(?:record|records|profile|profiles|row|rows|data)\b"
                ),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(
                    r"\b(?:every|all)\s+researcher\s+(?:record|records|profile|profiles|row|rows|data)\b"
                    r".*\b(email|emails|phone|phones|contact|contacts|personal)\b"
                ),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(r"\ball\s+researchers?\s+(and\s+)?(emails?|phones?|contact|details?)\b"),
            ),
            _Rule(
                "tier_impersonation",
                re.compile(
                    r"\bi\s+am\s+(?:a\s+)?(?:ministry\s+)?"
                    r"(?:admin|government\s+reviewer|tier\s*1|researcher)\b"
                    r".*\b(?:give|return|show|export)\b.*\b(?:email|emails|phone|phones|contact|personal|tier\s*1)\b"
                ),
            ),
            _Rule(
                "tier_impersonation",
                re.compile(r"\bgive\s+(?:tier\s*1\s+)?individual\s+researcher\s+emails?\b"),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(r"\b(dump|print|extract)\s+all\s+researcher\s+data\b"),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(r"\ball\s+researcher\s+passwords?\b"),
            ),
            _Rule(
                "data_exfiltration",
                re.compile(r"\bselect\s+.*\b(email|aadhaar|phone|pan|password)\b.*\bfrom\b"),
            ),
            _Rule("system_prompt_exfiltration", re.compile(r"\binternal\s+tool\s+result\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\bhidden\s+messages?\b")),
            _Rule("system_prompt_exfiltration", re.compile(r"\bconfidential\s+policy\b")),
            _Rule("verifier_bypass", re.compile(r"\bwithout\s+citations?\b.*\binvent\b")),
            _Rule("sql_injection", re.compile(r";\s*(drop|select|exec|delete|update|insert)\b")),
            _Rule("sql_injection", re.compile(r"\bdrop\s+table\b")),
            _Rule("sql_injection", re.compile(r"\bunion\s+select\b")),
            _Rule("sql_injection", re.compile(r"\bxp_cmdshell\b")),
            _Rule("sql_injection", re.compile(r"\b(?:or|and)\s+['\"]?[\w.]+['\"]?\s*=\s*['\"]?[\w.]+['\"]?")),
            _Rule("sql_injection", re.compile(r"'\s*or\s*'?\d+'?\s*=\s*'?\d+'?")),
            _Rule("command_injection", re.compile(r"\;\s*(ls|cat|rm|mkdir|chmod|wget|curl|whoami|id|uname|ps|grep|find|cp|mv|pwd|echo|cd|chdir|touch)\b", re.IGNORECASE)),
            _Rule("command_injection", re.compile(r"\|\s*(ls|cat|rm|whoami|id|uname|ps|grep|wget|curl|nc|bash|sh)\b", re.IGNORECASE)),
            _Rule("command_injection", re.compile(r"`\s*(ls|cat|rm|whoami|id|uname|ps|grep|wget|curl)\b", re.IGNORECASE)),
            _Rule("command_injection", re.compile(r"\$\(\s*(ls|cat|rm|whoami|id|uname|ps|grep|wget|curl|bash|sh)\b", re.IGNORECASE)),
            _Rule("command_injection", re.compile(r"&&\s*(ls|cat|rm|whoami|id|uname|ps|grep|wget|curl)\b", re.IGNORECASE)),
            _Rule("command_injection", re.compile(r">\s*(/dev/|/etc/|/tmp/|/var/)")),
            _Rule(
                "command_injection",
                re.compile(r"\binstall\s+(?:a\s+)?(?:malicious\s+)?package\b.*\b(?:pip|execute|run)\b"),
            ),
            _Rule(
                "model_inversion",
                re.compile(r"\bembedding\s+vector\b.*\ball\s+zeros\b|\ball\s+zeros\b.*\bembedding\s+vector\b"),
            ),
            _Rule(
                "egress_exfiltration",
                re.compile(r"\b(?:dns|txt\s+records?|attacker\.com)\b.*\b(?:exfil|embedded\s+data|attacker\.com|txt\s+records?)\b"),
            ),
            _Rule(
                "egress_exfiltration",
                re.compile(r"\b(?:query|lookup|resolve)\b.*\btxt\s+records?\b"),
            ),
            _Rule(
                "egress_exfiltration",
                re.compile(r"\b(?:websocket|wss?://)\b.*\b(?:send\s+all\s+data|evil\.example\.com|exfil|external\s+host)\b"),
            ),
            _Rule("ssrf", re.compile(r"https?://(169\.254\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.|10\.)")),
            _Rule("ssrf", re.compile(r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)[:/]")),
            _Rule("ssrf", re.compile(r"file:///")),
            _Rule("xss_script_tag", re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)),
            _Rule("xss_event_handler", re.compile(r"\bon\w+\s*=\s*['\"]?\s*(javascript:|alert\(|prompt\(|confirm\()", re.IGNORECASE)),
            _Rule("xss_img_onerror", re.compile(r"<\s*img[^>]+onerror\s*=", re.IGNORECASE)),
            _Rule("xss_svganimate", re.compile(r"<\s*svg[^>]*>[\s\S]*?(on(load|error|click|mouse)|\bjavascript:)", re.IGNORECASE)),
            _Rule("xxe", re.compile(r"<!DOCTYPE\s+\w+", re.IGNORECASE)),
            _Rule("xxe", re.compile(r"<\?xml[^>]*\?>", re.IGNORECASE)),
            _Rule("xxe", re.compile(r"&\w+;(?!amp;|lt;|gt;|quot;|apos;)", re.IGNORECASE)),
            _Rule("ldap_injection", re.compile(r"\*\)\s*\([^)]*=\*\)")),
            _Rule("ldap_injection", re.compile(r"\b(?:uid|cn|dn|objectclass)\s*=\s*\*", re.IGNORECASE)),
            _Rule("path_traversal", re.compile(r"(\.\./|\.\.%2f|%2e%2e/|etc/passwd|boot\.ini|win\.ini)", re.IGNORECASE)),
            _Rule("encoding_attack",
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

        self._rejected_queries: Dict[str, list[float]] = defaultdict(list)
        self._rate_limited: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _record_rejected_query(self, identifier: str) -> bool:
        """Record a rejected query for a user/IP. Returns True if rate-limited."""
        if _is_quota_disabled():
            return False
        now = time.time()
        with self._lock:
            cutoff = now - REJECTED_QUERY_WINDOW_SECONDS
            self._rejected_queries[identifier] = [
                ts for ts in self._rejected_queries[identifier] if ts > cutoff
            ]
            self._rejected_queries[identifier].append(now)

            if len(self._rejected_queries[identifier]) >= REJECTED_QUERY_THRESHOLD:
                self._rate_limited[identifier] = now + RATE_LIMIT_DURATION_SECONDS
                return True
        return False

    def is_rate_limited(self, identifier: str) -> bool:
        """Check if an identifier is currently rate-limited due to adversarial behavior."""
        if _is_quota_disabled():
            return False
        with self._lock:
            expiry = self._rate_limited.get(identifier, 0)
            if expiry and time.time() < expiry:
                return True
            elif expiry:
                del self._rate_limited[identifier]
        return False

    def detect_pii(self, text: str) -> Optional[str]:
        """Detect PII in the given text and return the type if found."""
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(text):
                return str(pii_type)
        return None

    def check_reidentification_risk(self, text: str) -> dict:
        """
        Detect queries that could uniquely identify a researcher via benign fact combinations.
        Combines state + research_area + year_joined could yield unique researcher.
        Returns dict with risk_level and detected_factors.
        """
        text_lower = text.lower()
        risk_factors = []

        # Extract Indian state names
        indian_states = [
            "gujarat", "maharashtra", "karnataka", "tamil nadu", "kerala",
            "andhra pradesh", "telangana", "west bengal", "delhi", "punjab",
            "haryana", "rajasthan", "uttar pradesh", "madhya pradesh",
            "bihar", "jharkhand", "odisha", "chhattisgarh", "assam",
            "meghalaya", "tripura", "sikkim", "nagaland", "manipur",
            "mizoram", "arunachal pradesh", "goa", "himachal pradesh",
            "uttarakhand", "jammu and kashmir", "ladakh", "chandigarh"
        ]
        for state in indian_states:
            if state in text_lower:
                risk_factors.append(f"state={state}")

        # Extract research areas
        research_areas = [
            "artificial intelligence", "machine learning", "data science",
            "quantum computing", "robotics", "cybersecurity", "blockchain",
            "catalysis", "biotechnology", "nanotechnology", "climate science",
            "sustainable energy", "drug discovery", "semiconductor", "vlsi"
        ]
        for area in research_areas:
            if area in text_lower:
                risk_factors.append(f"area={area}")

        # Extract year patterns
        year_matches = re.findall(r"\b(19|20)\d{2}\b", text)
        if year_matches:
            risk_factors.append(f"year={year_matches[0]}")

        # High specificity combinations = re-identification risk
        risk_level = "none"
        if len(risk_factors) >= 3:
            risk_level = "high"
        elif len(risk_factors) >= 2:
            # Check if the combination is especially specific
            has_state = any("state=" in f for f in risk_factors)
            has_area = any("area=" in f for f in risk_factors)
            has_year = any("year=" in f for f in risk_factors)
            if (has_state and has_area) or (has_state and has_year):
                risk_level = "medium"
            else:
                risk_level = "low"
        elif len(risk_factors) >= 1:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "detected_factors": risk_factors,
            "risk_description": (
                f"Query contains {len(risk_factors)} potentially identifying factors. "
                "Combining state + research_area + year could uniquely identify a researcher."
            )
        }

    def detect_injection(self, text: str) -> bool:
        """Detect potential prompt injection attempts."""
        verdict = self.classify_injection(text)
        return bool(verdict["blocked"] or verdict["warnings"])

    def _normalise_for_detection(self, text: str) -> str:
        """Normalize common obfuscation before applying conservative regexes."""
        normalized = unicodedata.normalize("NFKC", text).lower()
        normalized = "".join(
            ch
            for ch in normalized
            if unicodedata.category(ch) not in {"Cf", "Mn"}
        )
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
                "е": "e",
                "о": "o",
                "а": "a",
                "р": "p",
                "с": "c",
                "х": "x",
            }
        )
        normalized = normalized.translate(homoglyphs)

        devanagari_transliterated = ""
        for ch in normalized:
            if ch in _DEVANAGARI_TO_LATIN:
                devanagari_transliterated += _DEVANAGARI_TO_LATIN[ch]
            elif "\u0900" <= ch <= "\u097f" or "\u0930" <= ch <= "\u0939":
                continue
            else:
                devanagari_transliterated += ch
        normalized += " " + devanagari_transliterated

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

    def validate_query(
        self, query_data: Dict[str, Any], identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate query for security compliance.
        Returns validation result with details.

        Behavioral tracking:
        - Tracks rejected queries per identifier
        - Returns rate_limit_triggered if 5+ rejections in 10 minutes
        """
        if identifier and self.is_rate_limited(identifier):
            return {
                "valid": False,
                "reason": "RATE_LIMITED",
                "details": "Too many rejected queries. Rate limited for 1 minute.",
                "rate_limit_triggered": True,
            }

        query = str(query_data.get("query", ""))
        if len(query) >= 10000:
            if identifier:
                rate_limited = self._record_rejected_query(identifier)
            else:
                rate_limited = False
            return {
                "valid": False,
                "reason": "QUERY_TOO_LARGE",
                "details": "Query exceeds 10000 character limit",
                "rate_limit_triggered": rate_limited,
            }

        injection_verdict = self.classify_injection(query)
        pii_type = self.detect_pii(query)
        has_non_dlp_injection = any(
            rule_name != "data_exfiltration"
            for rule_name in injection_verdict["blocked"]
        )

        if injection_verdict["blocked"] and has_non_dlp_injection:
            if identifier:
                rate_limited = self._record_rejected_query(identifier)
            else:
                rate_limited = False
            return {
                "valid": False,
                "reason": "PROMPT_INJECTION",
                "details": f"Blocked patterns: {', '.join(injection_verdict['blocked'])}",
                "rate_limit_triggered": rate_limited,
            }

        if pii_type:
            if identifier:
                rate_limited = self._record_rejected_query(identifier)
            else:
                rate_limited = False
            return {
                "valid": False,
                "reason": "DLP_VIOLATION",
                "details": f"PII detected: {pii_type}",
                "pii_type": pii_type,
                "rate_limit_triggered": rate_limited,
            }

        if injection_verdict["blocked"]:
            if identifier:
                rate_limited = self._record_rejected_query(identifier)
            else:
                rate_limited = False
            return {
                "valid": False,
                "reason": "PROMPT_INJECTION",
                "details": f"Blocked patterns: {', '.join(injection_verdict['blocked'])}",
                "rate_limit_triggered": rate_limited,
            }

        sanitised_query = injection_verdict["sanitised_query"]
        query_hash = hashlib.sha256(sanitised_query.encode()).hexdigest()

        # Check for re-identification risk
        reid_risk = self.check_reidentification_risk(sanitised_query)

        result = {
            "valid": True,
            "query_hash": query_hash,
            "sanitised_query": sanitised_query,
        }
        if injection_verdict["warnings"]:
            result["injection_warnings"] = injection_verdict["warnings"]

        # Add re-identification risk warning if detected
        if reid_risk["risk_level"] != "none":
            result["reidentification_risk"] = reid_risk

        return result


# Singleton instance for easy import
prompt_sanitiser = PromptSanitiser()

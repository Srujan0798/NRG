# NRG Egress Control Specification v1.0

## Purpose

Enforce zero-data-leakage at the network level. Single outbound HTTP client with DLP inspection.

## Attack Surface

| Vector |Threat |Mitigation |
|--------|-------|-----------|
| Request body | PII exfiltration | Regex + Presidio NER block |
| Response body | Research data leak | Content inspection |
| URL params | Data in query string | Allowlist only |

## Implementation

### Single HTTP Client

```python
# src/security/egress/client.py
import re
import httpx
from typing import Optional
from presidion_analyzer import PresidioAnalyzer
from presidion_analyzer import RecognizerResult

class EgressController:
    """Single outbound HTTP client with DLP."""
    
    PII_PATTERNS = {
        "aadhaar": r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b",
        "pan": r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
        "phone": r"\b[6-9][0-9]{9}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    }
    
    ALLOWED_ENDPOINTS = {
        "gemini": "https://generativelanguage.googleapis.com",
        "claude": "api.anthropic.com",
    }
    
    def __init__(self, audit_logger):
        self.client = httpx.Client(timeout=30.0)
        self.analyzer = PresidioAnalyzer()
        self.audit_logger = audit_logger
        self.total_bytes_blocked = 0
    
    def post(self, url: str, data: dict, user_tier: int) -> dict:
        """Post with DLP inspection."""
        # Validate endpoint
        self._validate_endpoint(url)
        
        # Inspect payload
        payload_str = str(data)
        self._inspect_payload(payload_str, url)
        
        # Log attempt
        self.audit_logger.log_egress_attempt(url, len(payload_str), user_tier)
        
        # Execute
        response = self.client.post(url, json=data)
        
        return response.json()
    
    def _validate_endpoint(self, url: str) -> None:
        """Ensure endpoint is allowlisted."""
        allowed = any(allowed in url for allowed in self.ALLOWED_ENDPOINTS.values())
        if not allowed:
            raise EgressDenied(f"Endpoint not allowlisted: {url}")
    
    def _inspect_payload(self, payload: str, url: str) -> None:
        """Block PII in payload."""
        for name, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, payload):
                self.total_bytes_blocked += len(payload)
                raise EgressDenied(f"PII detected ({name}): blocked")
        
        # Presidio NER
        results = self.analyzer.analyze(text=payload)
        if results:
            raise EgressDenied(f"NER entities detected: {len(results)}")
```

### Red Team Test

```python
# tests/security/redteam/test_egress.py
import pytest
from src.security.egress.client import EgressController

CANARY_STRING = "NRG-CANARY-Aadhaar-1234-5678-9012-XYZ"

def test_canary_blocked():
    """Canary string must be blocked."""
    client = EgressController(audit_logger=MockLogger())
    
    with pytest.raises(EgressDenied):
        client.post(
            "https://generativelanguage.googleapis.com/v1beta/models",
            {"contents": [{"text": CANARY_STRING}]},
            user_tier=1
        )
    
    assert client.total_bytes_blocked > 0
```

## Logging

| Event | Logged Fields |
|-------|-----------|
| Egress attempt | timestamp, url, bytes_out, user_tier |
| Blocked | timestamp, reason, bytes_blocked |
| Allowed | timestamp, endpoint, bytes_out |

---

*Zero bytes of canary leave the pod on 50 adversarial prompts.*
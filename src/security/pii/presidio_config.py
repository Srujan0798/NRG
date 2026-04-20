"""Presidio PII detection with lazy loading to avoid import failures."""

from typing import List, Dict, Any


class PresidioConfig:
    """
    Configuration for Microsoft Presidio PII detection engine.
    Implements Indian-specific PII recognizers for DPDP 2023 compliance.
    """

    def __init__(self):
        self.nlp_engine = None
        self.analyzer = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return
        try:
            from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_analyzer.recognizer_registry import RecognizerRegistry
        except ImportError:
            self._initialized = True
            return

        self.nlp_engine = self._setup_nlp_engine(NlpEngineProvider)
        self.analyzer = self._setup_analyzer(
            AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
        )
        self._initialized = True

    def _setup_nlp_engine(self, NlpEngineProvider):
        provider = NlpEngineProvider()
        return provider.create_engine()

    def _setup_analyzer(self, AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern):
        registry = RecognizerRegistry()
        # Load all predefined recognizers (EMAIL, PHONE, CREDIT_CARD, etc.)
        registry.load_predefined_recognizers()

        # Indian PAN: 5 letters + 4 digits + 1 letter (e.g., ABCDE1234F)
        pan_recognizer = PatternRecognizer(
            supported_entity="IN_PAN",
            patterns=[
                Pattern(
                    name="pan_basic",
                    regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
                    score=0.9,
                )
            ],
            context=["pan", "permanent", "account", "number"],
            supported_language="en",
        )

        # Indian Aadhaar: 12 digits, often grouped as 4-4-4
        aadhaar_recognizer = PatternRecognizer(
            supported_entity="IN_AADHAAR",
            patterns=[
                Pattern(
                    name="aadhaar_grouped",
                    regex=r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b",
                    score=0.95,
                )
            ],
            context=["aadhaar", "uidai", "identity", "card"],
            supported_language="en",
        )

        registry.add_recognizer(pan_recognizer)
        registry.add_recognizer(aadhaar_recognizer)

        analyzer = AnalyzerEngine(
            nlp_engine=self.nlp_engine,
            registry=registry,
            default_score_threshold=0.5,
        )
        return analyzer

    def analyze_text(self, text: str, language: str = "en") -> List[Dict]:
        self._ensure_initialized()
        if self.analyzer is None:
            return self._fallback_analyze(text)

        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "CREDIT_CARD", "CRYPTO", "DATE_TIME", "EMAIL_ADDRESS",
                "IBAN_CODE", "IP_ADDRESS", "MEDICAL_LICENSE", "PERSON",
                "PHONE_NUMBER", "US_SSN", "URL", "IN_PAN", "IN_AADHAAR",
            ],
        )

        pii_entities = []
        for result in results:
            pii_entities.append({
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "text": text[result.start : result.end],
            })
        return pii_entities

    def _fallback_analyze(self, text: str) -> List[Dict]:
        results = []
        for recognizer in [_InPanRecognizer(), _InAadhaarRecognizer()]:
            for match in recognizer.analyze(text):  # type: ignore[attr-defined]
                results.append({
                    "entity_type": match["entity"],
                    "start": match["start"],
                    "end": match["end"],
                    "score": match["confidence"],
                    "text": text[match["start"]:match["end"]],
                })
        return results

    def get_supported_entities(self) -> List[str]:
        self._ensure_initialized()
        if self.analyzer is None:
            return ["IN_PAN", "IN_AADHAAR"]
        return list(self.analyzer.get_supported_entities())

    def validate_dpdp_compliance(self, text: str) -> Dict:
        pii_entities = self.analyze_text(text)

        compliance_report: dict[str, Any] = {
            "compliant": len(pii_entities) == 0,
            "pii_detected": len(pii_entities) > 0,
            "entities": pii_entities,
            "dpdp_violations": [],
        }

        for entity in pii_entities:
            compliance_report["dpdp_violations"].append({
                "type": entity["entity_type"],
                "text": entity["text"],
                "confidence": entity["score"],
                "violation": "PII detected without proper consent or processing basis",
            })

        return compliance_report


class _InPanRecognizer:
    """Indian PAN number recognizer (fallback when Presidio unavailable)."""

    def __init__(self):
        self.pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
        self.context = ["pan", "permanent", "account", "number"]

    def analyze(self, text: str):
        import re

        matches = re.finditer(self.pattern, text, re.IGNORECASE)
        results = []

        for match in matches:
            results.append({
                "entity": "IN_PAN",
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "confidence": 0.9,
            })

        return results


class _InAadhaarRecognizer:
    """Indian Aadhaar number recognizer (fallback when Presidio unavailable)."""

    def __init__(self):
        self.pattern = r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"
        self.context = ["aadhaar", "uidai", "identity", "card"]

    def analyze(self, text: str):
        import re

        matches = re.finditer(self.pattern, text)
        results = []

        for match in matches:
            results.append({
                "entity": "IN_AADHAAR",
                "start": match.start(),
                "end": match.end(),
                "text": match.group(),
                "confidence": 0.95,
            })

        return results


def _get_presidio_config() -> PresidioConfig:
    return PresidioConfig()

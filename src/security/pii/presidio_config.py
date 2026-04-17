import spacy
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    CryptoRecognizer,
    DateRecognizer,
    EmailRecognizer,
    IbanRecognizer,
    IpRecognizer,
    MedicalLicenseRecognizer,
    PersonRecognizer,
    PhoneRecognizer,
    SsnRecognizer,
    UrlRecognizer,
    InPanRecognizer,
    InAadhaarRecognizer,
)
from typing import List, Dict


class PresidioConfig:
    """
    Configuration for Microsoft Presidio PII detection engine.
    Implements Indian-specific PII recognizers for DPDP 2023 compliance.
    """

    def __init__(self):
        """Initialize Presidio analyzer with Indian-specific recognizers."""
        # Initialize NLP engine
        self.nlp_engine = self._setup_nlp_engine()
        self.analyzer = self._setup_analyzer()

    def _setup_nlp_engine(self):
        """Setup NLP engine for Presidio."""
        # Create NLP engine provider
        provider = NlpEngineProvider()
        return provider.create_engine()

    def _setup_analyzer(self):
        """Setup Presidio analyzer with custom recognizers."""
        # Create recognizer registry
        registry = RecognizerRegistry()

        # Add standard recognizers
        standard_recognizers = [
            CreditCardRecognizer(),
            CryptoRecognizer(),
            DateRecognizer(),
            EmailRecognizer(),
            IbanRecognizer(),
            IpRecognizer(),
            MedicalLicenseRecognizer(),
            PersonRecognizer(),
            PhoneRecognizer(),
            SsnRecognizer(),
            UrlRecognizer(),
        ]

        # Add Indian-specific recognizers
        indian_recognizers = [InPanRecognizer(), InAadhaarRecognizer()]

        # Combine all recognizers
        all_recognizers = standard_recognizers + indian_recognizers

        # Create analyzer engine
        analyzer = AnalyzerEngine(
            nlp_engine=self.nlp_engine, registry=registry, default_score_threshold=0.5
        )

        return analyzer

    def analyze_text(self, text: str, language: str = "en") -> List[Dict]:
        """Analyze text for PII entities."""
        # Analyze the text
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "CREDIT_CARD",
                "CRYPTO",
                "DATE_TIME",
                "EMAIL_ADDRESS",
                "IBAN_CODE",
                "IP_ADDRESS",
                "MEDICAL_LICENSE",
                "PERSON",
                "PHONE_NUMBER",
                "US_SSN",
                "URL",
                "IN_PAN",
                "IN_AADHAAR",
            ],
        )

        # Convert results to dictionary format
        pii_entities = []
        for result in results:
            pii_entities.append(
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start : result.end],
                }
            )

        return pii_entities

    def get_supported_entities(self) -> List[str]:
        """Get list of supported PII entities."""
        return self.analyzer.get_supported_entities()

    def validate_dpdp_compliance(self, text: str) -> Dict:
        """Validate text for DPDP 2023 compliance."""
        # Analyze for PII
        pii_entities = self.analyze_text(text)

        # Create compliance report
        compliance_report = {
            "compliant": len(pii_entities) == 0,
            "pii_detected": len(pii_entities) > 0,
            "entities": pii_entities,
            "dpdp_violations": [],
        }

        # Check for DPDP violations
        for entity in pii_entities:
            # Any PII detected is a potential violation unless properly handled
            compliance_report["dpdp_violations"].append(
                {
                    "type": entity["entity_type"],
                    "text": entity["text"],
                    "confidence": entity["score"],
                    "violation": "PII detected without proper consent or processing basis",
                }
            )

        return compliance_report


# Custom Indian PII Recognizers
class InPanRecognizer:
    """Indian PAN number recognizer."""

    def __init__(self):
        self.pattern = r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
        self.context = ["pan", "permanent", "account", "number"]

    def analyze(self, text: str):
        """Analyze text for PAN numbers."""
        import re

        matches = re.finditer(self.pattern, text, re.IGNORECASE)
        results = []

        for match in matches:
            results.append(
                {
                    "entity": "IN_PAN",
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "confidence": 0.9,
                }
            )

        return results


class InAadhaarRecognizer:
    """Indian Aadhaar number recognizer."""

    def __init__(self):
        self.pattern = r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"
        self.context = ["aadhaar", "uidai", "identity", "card"]

    def analyze(self, text: str):
        """Analyze text for Aadhaar numbers."""
        import re

        matches = re.finditer(self.pattern, text)
        results = []

        for match in matches:
            results.append(
                {
                    "entity": "IN_AADHAAR",
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "confidence": 0.95,
                }
            )

        return results


# Singleton instance
presidio_config = PresidioConfig()

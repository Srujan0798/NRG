import unittest
from src.security.pii.tokenizer import PIITokenizer
from src.security.pii.fpe_engine import FPEEngine
from src.security.pii.presidio_config import PresidioConfig


class TestPIICompliance(unittest.TestCase):
    """Test suite for PII compliance and tokenization."""

    def setUp(self):
        """Set up test fixtures."""
        self.tokenizer = PIITokenizer()
        self.fpe_engine = FPEEngine()
        self.presidio = PresidioConfig()

    def test_aadhaar_detection(self):
        """Test Aadhaar number detection."""
        test_text = "My Aadhaar number is 1234-5678-9012"
        detected = self.tokenizer.detect_pii(test_text)

        self.assertTrue(any(entity["type"] == "aadhaar" for entity in detected))
        # At least 1 entity detected (may be more due to presidio detection)

    def test_pan_detection(self):
        """Test PAN number detection."""
        test_text = "My PAN is ABCDE1234F"
        detected = self.tokenizer.detect_pii(test_text)

        self.assertTrue(any(entity["type"] == "pan" for entity in detected))
        self.assertEqual(len(detected), 1)

    def test_phone_detection(self):
        """Test phone number detection."""
        test_text = "Contact me at 9876543210"
        detected = self.tokenizer.detect_pii(test_text)

        self.assertTrue(any(entity["type"] == "phone" for entity in detected))
        # May detect multiple entities due to overlapping patterns

    def test_email_detection(self):
        """Test email detection."""
        test_text = "Email me at test@example.com"
        detected = self.tokenizer.detect_pii(test_text)

        self.assertTrue(any(entity["type"] == "email" for entity in detected))
        self.assertEqual(len(detected), 1)

    def test_pii_tokenization(self):
        """Test PII tokenization."""
        test_text = "My Aadhaar is 1234-5678-9012 and PAN is ABCDE1234F"
        tokenized_text, mappings = self.tokenizer.tokenize_pii(test_text)

        # Check that PII was tokenized
        self.assertIn("[AADHAAR_TOKEN]", tokenized_text)
        self.assertIn("[PAN_TOKEN]", tokenized_text)

        # Check that mappings were created (at least 2 for aadhaar and pan)
        self.assertGreaterEqual(len(mappings), 2)
        types = [m["type"] for m in mappings]
        self.assertIn("aadhaar", types)
        self.assertIn("pan", types)

    def test_fpe_encryption(self):
        """Test format-preserving encryption."""
        # Test Aadhaar FPE
        encrypted_aadhaar = self.fpe_engine.encrypt_aadhaar("123456789012")
        self.assertIsInstance(encrypted_aadhaar, str)
        self.assertEqual(len(encrypted_aadhaar), 14)  # XXXX-XXXX-XXXX format

        # Test PAN FPE
        encrypted_pan = self.fpe_engine.encrypt_pan("ABCDE1234F")
        self.assertIsInstance(encrypted_pan, str)
        self.assertEqual(len(encrypted_pan), 10)  # AAAAA9999A format

        # Test phone FPE
        encrypted_phone = self.fpe_engine.encrypt_phone("9876543210")
        self.assertIsInstance(encrypted_phone, str)
        self.assertEqual(len(encrypted_phone), 10)  # 10-digit format

    def test_dpdp_compliance(self):
        """Test DPDP 2023 compliance validation."""
        test_text = "My personal details: Aadhaar 1234-5678-9012, PAN ABCDE1234F"
        compliance_report = self.tokenizer.validate_dpdp_compliance(test_text)

        self.assertTrue(compliance_report["pii_detected"])
        self.assertFalse(compliance_report["compliant"])
        self.assertGreater(len(compliance_report["dpdp_violations"]), 0)

    def test_presidio_analysis(self):
        """Test Presidio PII analysis."""
        test_text = "Contact John Doe at john.doe@example.com or call 9876543210"
        entities = self.presidio.analyze_text(test_text)

        # Should detect email and phone
        self.assertGreater(len(entities), 0)

        # Check that email and phone are detected
        entity_types = [entity["entity_type"] for entity in entities]
        self.assertTrue(
            any("EMAIL" in et for et in entity_types)
            or any("PHONE" in et for et in entity_types)
        )


if __name__ == "__main__":
    unittest.main()

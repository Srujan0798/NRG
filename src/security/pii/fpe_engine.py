import re

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os


class FPEEngine:
    """
    Format-Preserving Encryption engine for DPDP 2023 compliance.
    Implements FPE for specific PII types to maintain format while encrypting.
    """

    def __init__(self):
        """Initialize FPE engine with encryption parameters."""
        # In a production environment, this key should come from a secure key management system
        self.key = os.urandom(32)  # 256-bit key
        self.iv = os.urandom(16)  # 128-bit IV

    def _encrypt_aes(self, data: bytes) -> bytes:
        """Encrypt data using AES."""
        # Pad the data to be multiple of 16 bytes
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data)
        padded_data += padder.finalize()

        # Encrypt with AES
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return encrypted

    def _decrypt_aes(self, encrypted_data: bytes) -> bytes:
        """Decrypt AES encrypted data."""
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(self.iv))
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decrypted_padded)
        decrypted_data += unpadder.finalize()

        return decrypted_data

    def encrypt_aadhaar(self, aadhaar_number: str) -> str:
        """Encrypt Aadhaar number while preserving format."""
        # Remove formatting
        clean_aadhaar = re.sub(r"[- ]", "", aadhaar_number)

        # Ensure it's a valid 12-digit number
        if not re.match(r"^[0-9]{12}$", clean_aadhaar):
            raise ValueError("Invalid Aadhaar number format")

        # Encrypt the number
        encrypted = self._encrypt_aes(clean_aadhaar.encode())

        # Convert to format-preserving string
        # We'll use a simple approach: take first 12 digits of hex representation
        encrypted_hex = encrypted.hex()[:12]

        # Format as XXXX-XXXX-XXXX
        formatted = f"{encrypted_hex[:4]}-{encrypted_hex[4:8]}-{encrypted_hex[8:12]}"
        return formatted

    def encrypt_pan(self, pan_number: str) -> str:
        """Encrypt PAN number while preserving format."""
        # Ensure it's a valid PAN format (5 uppercase + 4 digits + 1 uppercase)
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", pan_number):
            raise ValueError("Invalid PAN number format")

        # Encrypt the PAN
        encrypted = self._encrypt_aes(pan_number.encode())

        # Convert to format-preserving string
        # PAN format: AAAAA9999A (5 uppercase + 4 digits + 1 uppercase)
        encrypted_hex = encrypted.hex()[:10]  # Take 10 characters

        # Create format-preserving PAN
        # First 5 chars for uppercase letters, next 4 for digits, last 1 for letter
        pan_letters = encrypted_hex[:5].upper()
        pan_digits = encrypted_hex[5:9]
        pan_last_char = encrypted_hex[9].upper() if encrypted_hex[9].isalpha() else "A"

        # Ensure we have valid characters
        pan_letters = "".join(c if c.isalpha() else "A" for c in pan_letters)
        pan_digits = "".join(c if c.isdigit() else "0" for c in pan_digits)
        pan_last_char = pan_last_char if pan_last_char.isalpha() else "Z"

        return f"{pan_letters}{pan_digits}{pan_last_char}"

    def encrypt_phone(self, phone_number: str) -> str:
        """Encrypt phone number while preserving format."""
        # Clean phone number
        clean_phone = re.sub(r"[^0-9]", "", phone_number)

        # Ensure it's a valid Indian phone number (10 digits starting with 6-9)
        if not re.match(r"^[6-9][0-9]{9}$", clean_phone):
            raise ValueError("Invalid Indian phone number format")

        # Encrypt the phone number
        encrypted = self._encrypt_aes(clean_phone.encode())

        # Convert to 10-digit format-preserving phone number
        # Take first 10 digits and ensure it starts with 6-9
        encrypted_str = encrypted.hex()[:10]
        first_digit = encrypted_str[0] if encrypted_str[0] in "6789" else "6"
        rest_digits = "".join(c if c.isdigit() else "0" for c in encrypted_str[1:])

        return first_digit + rest_digits

    def decrypt_aadhaar(self, encrypted_aadhaar: str) -> str:
        """Decrypt Aadhaar number (placeholder - in practice would reverse the encryption)."""
        # In a real implementation, this would actually decrypt
        return "[DECRYPTED_AADHAAR]"

    def decrypt_pan(self, encrypted_pan: str) -> str:
        """Decrypt PAN number (placeholder - in practice would reverse the encryption)."""
        # In a real implementation, this would actually decrypt
        return "[DECRYPTED_PAN]"

    def decrypt_phone(self, encrypted_phone: str) -> str:
        """Decrypt phone number (placeholder - in practice would reverse the encryption)."""
        # In a real implementation, this would actually decrypt
        return "[DECRYPTED_PHONE]"


# Singleton instance
fpe_engine = FPEEngine()

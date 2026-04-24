"""Verhoeff checksum validation for Indian Aadhaar numbers.

The Verhoeff algorithm is a checksum formula that detects any single-digit
error and all adjacent transpositions. Required by DPDP compliance for
Aadhaar number validation before any masking or processing.
"""

VERHOEFF_TABLE = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

VERHOEFF_PERM = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 8, 5),
)


def validate_verhoeff(digits: str) -> bool:
    """Validate a digit string using Verhoeff checksum.

    Args:
        digits: String of digits (e.g., "123456789012")

    Returns:
        True if valid Verhoeff checksum, False otherwise.
    """
    if not digits or not digits.isdigit():
        return False

    checksum = 0
    for i, d in enumerate(reversed(digits)):
        checksum = VERHOEFF_TABLE[checksum][VERHOEFF_PERM[i % 8][int(d)]]

    return checksum == 0


def validate_aadhaar(aadhaar: str) -> bool:
    """Validate an Aadhaar number using Verhoeff checksum.

    Args:
        aadhaar: Aadhaar string, may contain spaces or dashes.

    Returns:
        True if valid Aadhaar (12 digits + valid Verhoeff), False otherwise.
    """
    cleaned = aadhaar.replace(" ", "").replace("-", "")

    if len(cleaned) != 12:
        return False

    if not cleaned.isdigit():
        return False

    return validate_verhoeff(cleaned)

"""Database identifier validation helpers."""

MAX_POSTGRES_IDENTIFIER_BYTES = 63


def validate_identifier(name: str) -> str:
    """Return a valid PostgreSQL identifier or raise before truncation risk."""
    if len(name.encode("utf-8")) > MAX_POSTGRES_IDENTIFIER_BYTES:
        raise ValueError(f"Identifier {name!r} exceeds 63 bytes")
    return name

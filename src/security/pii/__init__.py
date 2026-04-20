"""PII scanning helpers with spaCy-first and regex fallback behavior."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from .fpe_engine import FPEEngine
from .presidio_config import PresidioConfig
from .tokenizer import PIITokenizer

_PII_REGEX = {
    "aadhaar": re.compile(r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b"),
    "pan": re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE),
    "phone": re.compile(r"\b[6-9][0-9]{9}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}


@lru_cache(maxsize=1)
def _load_spacy_model() -> Any | None:
    try:
        import spacy

        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _scan_with_regex(text: str) -> list[dict[str, Any]]:
    detections: list[dict[str, Any]] = []
    for pii_type, pattern in _PII_REGEX.items():
        for match in pattern.finditer(text):
            detections.append(
                {
                    "type": pii_type,
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "source": "regex",
                }
            )
    return detections


def _scan_with_spacy(text: str) -> list[dict[str, Any]]:
    nlp = _load_spacy_model()
    if nlp is None:
        return []

    doc = nlp(text)
    detections: list[dict[str, Any]] = []

    for token in doc:
        if token.like_email:
            detections.append(
                {
                    "type": "email",
                    "value": token.text,
                    "start": token.idx,
                    "end": token.idx + len(token.text),
                    "source": "spacy",
                }
            )

    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG"}:
            continue
        detections.append(
            {
                "type": ent.label_.lower(),
                "value": ent.text,
                "start": ent.start_char,
                "end": ent.end_char,
                "source": "spacy",
            }
        )

    return detections


def scan(text: str) -> dict[str, Any]:
    """Detect PII entities. Falls back to regex-only if spaCy model is unavailable."""
    regex_hits = _scan_with_regex(text)
    spacy_hits = _scan_with_spacy(text)

    deduped: dict[tuple[str, int, int], dict[str, Any]] = {}
    for hit in [*regex_hits, *spacy_hits]:
        key = (str(hit["type"]), int(hit["start"]), int(hit["end"]))
        deduped[key] = hit

    entities = list(deduped.values())
    return {
        "detected_pii": len(entities) > 0,
        "entities": entities,
        "mode": "spacy+regex" if _load_spacy_model() is not None else "regex_only",
    }


__all__ = [
    "scan",
    "PIITokenizer",
    "FPEEngine",
    "PresidioConfig",
]

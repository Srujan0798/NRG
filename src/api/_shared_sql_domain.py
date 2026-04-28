"""Shared SQL domain hint extractors — deduplicated helpers for academic_courses_details queries."""

from __future__ import annotations

import re


def extract_institute_hint(query: str) -> str | None:
    match = re.search(r"\b(IIT\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)\b", query, flags=re.IGNORECASE)
    if match:
        parts = match.group(1).split()
        while len(parts) > 2 and parts[-1].lower() in {"offer", "offered", "offers", "has", "have", "had"}:
            parts.pop()
        return " ".join(part.capitalize() if part.lower() != "iit" else "IIT" for part in parts)
    return None


def extract_year_hint(query: str) -> str | None:
    match = re.search(r"\b(20\d{2})(?:[-/](\d{2}))?\b", query)
    if not match:
        return None
    start = int(match.group(1))
    if match.group(2):
        return f"{start}-{match.group(2)}"
    return f"{start}-{str(start + 1)[-2:]}"


def previous_financial_year(financial_year: str | None) -> str | None:
    if not financial_year or "-" not in financial_year:
        return None
    try:
        start_text, end_text = financial_year.split("-", 1)
        start = int(start_text)
        end = int(end_text)
    except ValueError:
        return None
    return f"{start - 1}-{(end - 1) % 100:02d}"

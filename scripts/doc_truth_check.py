#!/usr/bin/env python3
"""Check current source-of-truth docs for unsupported completion claims."""

import re
import sys
from pathlib import Path

PROBLEMS = []

CANONICAL_DOCS = [
    Path("README.md"),
    Path("Core_Idea_Clean.md"),
    Path("docs/architecture/ARCHITECTURE.md"),
    Path("docs/architecture/SYNTHESIS_DECISION.md"),
]

CHECKS = [
    (r"REPLACE_ME", "placeholder secret"),
    (r"sk-IITGN-prod", "fake production key"),
    (r"\bProduction Ready\b", "unsupported production readiness claim"),
    (r"\bCertified\b", "unsupported certification claim"),
    (r"p95\s*[<>=]\s*\d+\s*ms", "unsupported p95 latency claim"),
    (r"benchmark(?:ed|s)?\s+(?:passed|complete|verified|certified)", "unsupported benchmark completion claim"),
]

def check_file(filepath: Path, pattern: str, description: str):
    """Check a file for a pattern and report issues."""
    if not filepath.exists():
        return
    content = filepath.read_text()
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
    if matches:
        for match in matches:
            PROBLEMS.append(f"{filepath}: {description} found: {match[:80]}")

def main():
    for doc in CANONICAL_DOCS:
        for pattern, description in CHECKS:
            check_file(doc, pattern, description)

    if PROBLEMS:
        print("ISSUES FOUND:")
        for p in PROBLEMS:
            print(f"  - {p}")
        return 1
    else:
        print("PASS: No unsupported claims found in user-facing docs")
        return 0

if __name__ == "__main__":
    sys.exit(main())

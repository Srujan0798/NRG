#!/usr/bin/env python3
"""
doc_truth_check.py - AGENT-TASK-39 Acceptance Script
Verifies docs have no unsupported claims: REPLACE_ME, sk-IITGN-prod, p95 claims.
"""
import os
import re
import sys
from pathlib import Path

DOCS_DIR = Path("docs")
README = Path("README.md")

PROBLEMS = []

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
    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        print("Dry-run mode. Use -- to actually delete or pass --help")
        return

    # Check for REPLACE_ME in user-facing docs (exclude .env.example, agent internal docs)
    EXCLUDEDIRS = {".agents", "AGENT_AUDIT_PROMPT.md", "AUDIT_V3_FINAL.md", ".protocol"}
    EXCLUDED_FILES = {".env.example"}

    for md in DOCS_DIR.rglob("*.md"):
        if any(excluded in str(md) for excluded in EXCLUDEDIRS):
            continue
        if md.name in EXCLUDED_FILES:
            continue

        check_file(md, r"REPLACE_ME", "REPLACE_ME placeholder")
        check_file(md, r"sk-IITGN-prod", "fake production key")
        check_file(md, r"p95\s*[<>=]\s*\d+\s*ms", "unsupported p95 latency claim")

    # Check README specifically
    check_file(README, r"REPLACE_ME", "REPLACE_ME placeholder")
    check_file(README, r"sk-IITGN-prod", "fake production key")
    check_file(README, r"p95\s*[<>=]\s*\d+\s*ms", "unsupported p95 latency claim")

    if PROBLEMS:
        print("ISSUES FOUND:")
        for p in PROBLEMS:
            print(f"  - {p}")
        return 1
    else:
        print("PASS: No unsupported claims found in docs")
        return 0

if __name__ == "__main__":
    sys.exit(main())
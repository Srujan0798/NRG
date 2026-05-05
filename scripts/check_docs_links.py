#!/usr/bin/env python3
"""Check internal Markdown links in documentation files.

External URLs are intentionally skipped because this gate is meant to catch
stale repo paths before handover. By default it scans the public documentation
surface plus the root README and script/corpus indexes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = (
    "docs",
    "README.md",
    "CORPUS/README.md",
    "scripts/README.md",
    ".claude/quality-bar.md",
)
SKIP_PARTS = {".git", ".venv", "node_modules", "__pycache__"}
LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def iter_markdown_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = (REPO_ROOT / target).resolve()
        if not path.exists():
            files.append(path)
            continue
        if path.is_file() and path.suffix.lower() == ".md":
            files.append(path)
            continue
        if path.is_dir():
            for candidate in path.rglob("*.md"):
                if SKIP_PARTS.intersection(candidate.parts):
                    continue
                files.append(candidate.resolve())
    return sorted(files)


def normalize_target(raw: str) -> str | None:
    target = raw.strip()
    if not target:
        return None
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target:
        # Markdown allows optional title text after the path.
        target = target.split(" ", 1)[0]
    target = unquote(target.strip())
    if not target or target.startswith("#"):
        return None
    lowered = target.lower()
    if lowered.startswith(("http://", "https://", "mailto:", "tel:")):
        return None
    if SCHEME_RE.match(target):
        return None
    return target.split("#", 1)[0].split("?", 1)[0]


def resolve_target(source: Path, target: str) -> Path:
    if target.startswith("/"):
        return (REPO_ROOT / target.lstrip("/")).resolve()
    return (source.parent / target).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", default=list(DEFAULT_TARGETS))
    args = parser.parse_args()

    broken: list[str] = []
    scanned_links = 0
    markdown_files = iter_markdown_files(args.targets)

    for source in markdown_files:
        if not source.exists():
            broken.append(f"MISSING_SCAN_TARGET {source.relative_to(REPO_ROOT)}")
            continue
        for line_number, line in enumerate(source.read_text(errors="replace").splitlines(), start=1):
            for match in LINK_RE.finditer(line):
                normalized = normalize_target(match.group(1))
                if normalized is None:
                    continue
                scanned_links += 1
                resolved = resolve_target(source, normalized)
                if not resolved.exists():
                    rel_source = source.relative_to(REPO_ROOT)
                    broken.append(f"{rel_source}:{line_number} -> {match.group(1)}")

    if broken:
        print("broken internal markdown links:")
        for item in broken:
            print(f"- {item}")
        print(f"scanned_links={scanned_links}")
        return 1

    print(f"docs link integrity: OK ({len(markdown_files)} files, {scanned_links} internal links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
NRG Workflow Validator
Checks .claude/ and .agents/ structure for bloat, duplicates, and stale refs.
Run this after any workflow change or on a fresh clone.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")


def ok(msg: str) -> None:
    print(f"OK:   {msg}")


def check_skill_counts() -> int:
    errors = 0
    claude_skills = sorted([d.name for d in (REPO_ROOT / ".claude" / "skills").iterdir() if d.is_dir()])
    agents_skills = sorted([d.name for d in (REPO_ROOT / ".agents" / "skills").iterdir() if d.is_dir()])

    total = len(claude_skills) + len(agents_skills)
    ok(f".claude/skills: {len(claude_skills)}, .agents/skills: {len(agents_skills)}, total: {total}")

    if total > 150:
        fail(f"Skill count {total} exceeds threshold 150. Consolidate skills.")
        errors += 1

    duplicates = set(claude_skills) & set(agents_skills)
    if duplicates:
        for dup in sorted(duplicates):
            fail(f"Duplicate skill across .claude and .agents: {dup}")
            errors += 1
    else:
        ok("No duplicate skill names across .claude and .agents")

    return errors


def check_manifest_freshness() -> int:
    errors = 0
    manifest = REPO_ROOT / ".claude" / "MANIFEST.md"
    if not manifest.exists():
        fail("MANIFEST.md missing")
        return 1

    content = manifest.read_text()
    # Check for stale claims from the pre-consolidation inventory.
    if "65" in content and "unique skills" in content:
        fail("MANIFEST.md claims 65 skills - run nrg-skill-count.py and update it")
        errors += 1
    if "2026-04-25" in content:
        fail("MANIFEST.md last updated 2026-04-25 - stale")
        errors += 1

    if errors == 0:
        ok("MANIFEST.md appears current")
    return errors


def check_forbidden_vocabulary() -> int:
    checker = REPO_ROOT / "scripts" / "forbidden_vocab_check.sh"
    if not checker.exists():
        fail("scripts/forbidden_vocab_check.sh missing")
        return 1

    result = subprocess.run(
        ["bash", str(checker), "--all"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode == 0:
        ok("Forbidden vocabulary guard passed")
        return 0

    fail("Forbidden vocabulary guard failed")
    for line in result.stdout.splitlines()[:20]:
        print(f"      {line}")
    return 1


def check_stale_evidence() -> int:
    errors = 0
    evidence_root = REPO_ROOT / "evidence"
    if not evidence_root.exists():
        ok("No evidence folder")
        return 0

    total_size = sum(f.stat().st_size for f in evidence_root.rglob("*") if f.is_file())
    if total_size > 200 * 1024 * 1024:
        fail(f"Evidence folder is {total_size / (1024*1024):.1f} MB (> 200 MB). Run nrg-evidence-prune.py")
        errors += 1
    else:
        ok(f"Evidence folder size: {total_size / (1024*1024):.1f} MB")

    # Count files older than 14 days
    import time
    now = time.time()
    cutoff = 14 * 86400
    stale = 0
    for fpath in evidence_root.rglob("*"):
        if fpath.is_file() and (now - fpath.stat().st_mtime) > cutoff:
            stale += 1
    if stale > 500:
        fail(f"{stale} evidence files older than 14 days. Run nrg-evidence-prune.py")
        errors += 1
    else:
        ok(f"Stale evidence files: {stale}")
    return errors


def check_hardcoded_paths() -> int:
    errors = 0
    scripts = list((REPO_ROOT / "scripts").glob("*.py")) + list((REPO_ROOT / "scripts").glob("*.sh"))
    for spath in scripts:
        text = spath.read_text(encoding="utf-8", errors="ignore")
        if "/Users/srujansai/Desktop/NRG" in text:
            fail(f"Hardcoded path in {spath.relative_to(REPO_ROOT)}")
            errors += 1
    if errors == 0:
        ok("No hardcoded /Users/srujansai/Desktop/NRG paths in scripts")
    return errors


def check_assignment_format() -> int:
    errors = 0
    assignments_dir = REPO_ROOT / ".claude" / "assignments"
    if not assignments_dir.exists():
        ok("No .claude/assignments/ directory")
        return 0

    # Hybrid format: Codex 5.5 framing + NRG execution mechanics
    required_sections = [
        "Role",
        "Personality",
        "Goal",
        "FILES",
        "PROBLEM",
        "STEPS",
        "SKILLS",
        "Constraints",
        "EVIDENCE",
        "DONE WHEN",
        "Stop Rules",
    ]
    for fpath in assignments_dir.glob("*.md"):
        text = fpath.read_text(encoding="utf-8", errors="ignore")
        missing = [s for s in required_sections if s not in text]
        if missing:
            fail(f"Assignment {fpath.name} missing hybrid sections: {', '.join(missing)}")
            errors += 1

        # Validate referenced skill files exist
        import re
        skill_refs = re.findall(r"`?((?:\.agents|\.claude)/skills/[^`/\s]+)/SKILL\.md`?", text)
        for skill_dir in skill_refs:
            skill_path = REPO_ROOT / skill_dir / "SKILL.md"
            if not skill_path.exists():
                fail(f"Assignment {fpath.name} references missing skill: {skill_dir}/SKILL.md")
                errors += 1

    if errors == 0:
        ok("Assignment files follow hybrid format (Codex 5.5 + NRG)")
    return errors


def check_entry_points() -> int:
    errors = 0
    required = [
        REPO_ROOT / ".claude" / "CLAUDE.md",
        REPO_ROOT / ".agents" / "AGENTS.md",
        REPO_ROOT / ".claude" / "CURRENT_STATE.md",
        REPO_ROOT / "AGENTS.md",
    ]
    for p in required:
        if not p.exists():
            fail(f"Missing entry point: {p.relative_to(REPO_ROOT)}")
            errors += 1
    if errors == 0:
        ok("All entry points present")
    return errors


def main() -> int:
    print("=" * 60)
    print("NRG Workflow Validator")
    print("=" * 60)

    total_errors = 0
    total_errors += check_entry_points()
    total_errors += check_skill_counts()
    total_errors += check_manifest_freshness()
    total_errors += check_forbidden_vocabulary()
    total_errors += check_stale_evidence()
    total_errors += check_hardcoded_paths()
    total_errors += check_assignment_format()

    print("=" * 60)
    if total_errors == 0:
        print("ALL CHECKS PASSED - workflow is clean")
        return 0
    else:
        print(f"FOUND {total_errors} ISSUE(S) - fix before continuing")
        return 1


if __name__ == "__main__":
    sys.exit(main())

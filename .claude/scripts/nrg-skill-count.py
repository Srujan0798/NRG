#!/usr/bin/env python3
"""
NRG Skill Counter
Counts skills in .claude/skills/ and .agents/skills/, flags duplicates.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    claude_dir = REPO_ROOT / ".claude" / "skills"
    agents_dir = REPO_ROOT / ".agents" / "skills"

    claude_skills = sorted([d.name for d in claude_dir.iterdir() if d.is_dir()])
    agents_skills = sorted([d.name for d in agents_dir.iterdir() if d.is_dir()])

    print("NRG Skill Inventory")
    print("=" * 50)
    print(f".claude/skills:  {len(claude_skills)}")
    print(f".agents/skills:  {len(agents_skills)}")
    print(f"TOTAL:           {len(claude_skills) + len(agents_skills)}")
    print("=" * 50)

    duplicates = set(claude_skills) & set(agents_skills)
    if duplicates:
        print(f"\nDUPLICATES ({len(duplicates)}):")
        for dup in sorted(duplicates):
            print(f"  - {dup}")
        return 1
    else:
        print("\nNo duplicates found.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

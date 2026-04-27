#!/usr/bin/env python3
"""Package the NRG data analyst skill into a distributable .zip."""

import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[2]
OUTPUT = SKILL_DIR.parents[1] / "nrg-data-analyst.zip"

with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in SKILL_DIR.rglob("*"):
        if f.is_file() and ".DS_Store" not in f.name and "__pycache__" not in str(f):
            arcname = f.relative_to(SKILL_DIR.parent)
            zf.write(f, arcname)
            print(f"  Added: {arcname}")

print(f"\nPackaged to: {OUTPUT}")

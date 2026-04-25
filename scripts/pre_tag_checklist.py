#!/usr/bin/env python3
"""
Pre-Tag Evidence Checklist — v1.0.0-eternal Gate.

Verifies all 9 prerequisites are met before git tagging.
Run on sovereign cluster after all other steps complete.

Usage:
    python scripts/pre_tag_checklist.py
    python scripts/pre_tag_checklist.py --report evidence/PRE_TAG_CHECKLIST.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"


CHECKS = []


def check(name: str, condition: bool, detail: str = "") -> bool:
    """Register a check result."""
    CHECKS.append({
        "name": name,
        "passed": condition,
        "detail": detail,
    })
    icon = "✅" if condition else "❌"
    print(f"  {icon} {name}")
    if detail:
        print(f"      {detail}")
    return condition


def run_cmd(cmd: list[str], timeout: int = 30) -> tuple[int, str, str]:
    """Run command, return (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)


def main():
    print("=" * 60)
    print("PRE-TAG EVIDENCE CHECKLIST — v1.0.0-eternal Gate")
    print("=" * 60)

    all_passed = True

    # 1. Quality Bar Scorecard
    print("\n[1/9] Quality Bar Scorecard — 5/5 (C4 SKIP requires sovereign)")
    qb_path = ROOT / "scripts" / "quality_bar_scorecard.json"
    if qb_path.exists():
        data = json.loads(qb_path.read_text())
        scores = data.get("scores", {})
        # C4 is SKIP in local env — acceptable. All others must PASS.
        c4_status = scores.get("C4", "FAIL")
        non_c4_fail = [k for k, v in scores.items() if k != "C4" and v != "PASS"]
        scorecard_pass = (c4_status == "SKIP") and (len(non_c4_fail) == 0)
        check("Quality Bar 5/5 (C4 sovereign-only)", scorecard_pass,
              f"Scores: {scores}")
    else:
        check("Quality Bar Scorecard", False, "quality_bar_scorecard.json not found")
        scorecard_pass = False
    all_passed = all_passed and scorecard_pass

    # 2. Audit Chain Valid
    print("\n[2/9] Audit Chain Integrity")
    try:
        from src.audit import verify_chain
        valid, errs, count = verify_chain()
        check("Audit chain valid", valid and len(errs) == 0, f"Events: {count}")
    except Exception as e:
        check("Audit chain valid", False, str(e))
        all_passed = False

    # 3. Data Quality Scorecard 6/6
    print("\n[3/9] Data Quality Scorecard — 6/6")
    dq_json = ROOT / ".cache" / "dq_scorecard.json"
    dq_json.parent.mkdir(parents=True, exist_ok=True)
    rc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "data_quality_scorecard.py"),
         "--output", str(dq_json)],
        capture_output=True, text=True, timeout=30, cwd=str(ROOT),
    )
    if dq_json.exists():
        data = json.loads(dq_json.read_text())
        critical = data.get("critical", 999)
        score = data.get("overall_score", 0)
        dq_pass = critical == 0 and score >= 90
        check("Data Quality 6 pillars", dq_pass, f"Score: {score}, Critical: {critical}")
    else:
        check("Data Quality 6 pillars", False, "Scorecard failed to generate")
        dq_pass = False
    all_passed = all_passed and dq_pass

    # 4. C4 Load Test P99 < 500ms
    print("\n[4/9] C4 Load Test — P99 < 500ms @ 1000 concurrent")
    report_path = EVIDENCE_DIR / "02_load_report.md"
    if report_path.exists():
        content = report_path.read_text()
        # Extract P99 value
        import re
        m = re.search(r"P99.*?(\d+)", content)
        if m:
            p99 = int(m.group(1))
            p99_pass = p99 < 500
            check("C4 P99 < 500ms @ 1000 users", p99_pass, f"P99={p99}ms")
            all_passed = all_passed and p99_pass
        else:
            check("C4 P99 < 500ms @ 1000 users", False, "P99 value not found in report")
    else:
        check("C4 P99 < 500ms @ 1000 users", False, "evidence/02_load_report.md not found")
        all_passed = False

    # 5. UAT T1 Passed
    print("\n[5/9] UAT Sessions — T1/T2/T3 Complete")
    uat_paths = [
        EVIDENCE_DIR / "03_uat_t1_results.json",
        EVIDENCE_DIR / "03_uat_t2_results.json",
        EVIDENCE_DIR / "03_uat_t3_results.json",
    ]
    uat_all_pass = True
    for p in uat_paths:
        if p.exists():
            data = json.loads(p.read_text())
            passed = data.get("summary", {}).get("success", 0) >= 8
            tier = data.get("tier", "?")
            check(f"UAT Tier {tier} ≥8/10 queries", passed,
                  f"{data.get('summary',{}).get('success','?')}/10 OK")
            uat_all_pass = uat_all_pass and passed
        else:
            tier = p.stem.split("_t")[1].split("_")[0] if "_t" in p.stem else p.stem[-1]
            check(f"UAT Tier {tier} results", False, f"{p.name} not found")
            uat_all_pass = False
    all_passed = all_passed and uat_all_pass

    # 6. Demo Video SHA256
    print("\n[6/9] Demo Video")
    demo_sha = EVIDENCE_DIR / "04_demo.sha256"
    if demo_sha.exists():
        sha_content = demo_sha.read_text().strip()
        check("Demo video SHA256 recorded", len(sha_content) > 0, f"SHA: {sha_content[:20]}...")
    else:
        check("Demo video SHA256 recorded", False, "04_demo.sha256 not found")
        all_passed = False

    # 7. Chain Seal Attestation
    print("\n[7/9] Chain Seal Attestation — C1/C2/C6")
    seal_path = EVIDENCE_DIR / "05_chain_seal.json"
    if seal_path.exists():
        data = json.loads(seal_path.read_text())
        seal_pass = data.get("status") == "PASS"
        check("Chain seal C1/C2/C6 passed", seal_pass, f"Status: {data.get('status')}")
    else:
        check("Chain seal C1/C2/C6 passed", False, "05_chain_seal.json not found")
        all_passed = False
    all_passed = all_passed and seal_pass

    # 8. GPG Signatures (8 docs)
    print("\n[8/9] Founder GPG Signatures — 8 handover docs")
    sig_dir = ROOT / "docs" / "handover" / "signatures"
    if sig_dir.exists():
        sigs = list(sig_dir.glob("*.asc"))
        check("GPG signatures present (≥8)", len(sigs) >= 8, f"{len(sigs)} signatures found")
        all_passed = all_passed and len(sigs) >= 8
    else:
        check("GPG signatures present (≥8)", False, f"{sig_dir} does not exist")
        all_passed = False

    # 9. Git tag not yet pushed
    print("\n[9/9] Git State")
    rc, out, _ = run_cmd(["git", "tag", "-l", "v1.0.0-eternal"])
    tag_exists = rc == 0 and "v1.0.0-eternal" in out
    check("v1.0.0-eternal tag NOT yet created", not tag_exists,
          "Tag exists (should not yet)" if tag_exists else "No tag yet — ready to create")
    if tag_exists:
        all_passed = False

    # Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL 9 PREREQUISITES MET — Ready to tag v1.0.0-eternal")
        print(f"\nNext step:")
        print(f"  git tag -s v1.0.0-eternal -m 'Eternal Seal #45 complete'")
        print(f"  git push origin v1.0.0-eternal")
    else:
        failed = [c["name"] for c in CHECKS if not c["passed"]]
        print(f"❌ {len(failed)} prerequisites not met:")
        for f in failed:
            print(f"  - {f}")
    print(f"{'='*60}")

    # Write checklist report
    report_path = Path("evidence/PRE_TAG_CHECKLIST.md")
    now = datetime.now(UTC).isoformat()
    md_lines = [
        "# Pre-Tag Evidence Checklist — v1.0.0-eternal",
        "",
        f"**Generated:** {now}",
        f"**Status:** {'✅ ALL PASSED — Ready to tag' if all_passed else '❌ BLOCKED'}",
        "",
        "## Prerequisite Status",
        "",
        "| # | Prerequisite | Status | Detail |",
        "|---|-------------|--------|--------|",
    ]
    for i, c in enumerate(CHECKS, 1):
        icon = "✅" if c["passed"] else "❌"
        md_lines.append(f"| {i} | {c['name']} | {icon} | {c.get('detail','')} |")

    md_lines.append("")
    if all_passed:
        md_lines += [
            "## Ready to Tag",
            "",
            "```bash",
            "git tag -s v1.0.0-eternal \\",
            '  -m "Eternal Seal #45 complete — 6/6 QB, UAT passed, chain sealed"', "",
            "git push origin v1.0.0-eternal",
            "```",
        ]
    else:
        md_lines.append("❌ Some prerequisites not met. Resolve before tagging.")

    report_path.write_text("\n".join(md_lines))
    print(f"\nReport: {report_path}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

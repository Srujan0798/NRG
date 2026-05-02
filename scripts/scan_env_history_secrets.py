#!/usr/bin/env python3
"""Scan Git history for secret-like assignments in runtime .env files.

The scanner never prints secret values. It reports commit, path, line number,
key name, value length, and a short hash fingerprint for triage.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


RUNTIME_ENV_BASENAMES = (
    ".env",
    ".env.dev",
    ".env.local",
    ".env.prod",
    ".env.staging",
    ".env.production",
)

ASSIGNMENT_RE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
SECRET_KEY_RE = re.compile(
    r"(PASSWORD|PASSCODE|SECRET|TOKEN|API_KEY|PRIVATE_KEY(?!_PATH)|CLIENT_SECRET|"
    r"ACCESS_KEY|DATABASE_URL|REDIS_URL|DSN|HMAC_SECRET)",
    re.IGNORECASE,
)
PLACEHOLDER_RE = re.compile(
    r"^(|changeme|change_me|change-me|placeholder|example|sample|replace_me|"
    r"replace-me|redacted|none|null|todo|set_me|set-me|your[-_ ].*|<.*>|\$\{.*\}|x{4,})$",
    re.IGNORECASE,
)


@dataclasses.dataclass(frozen=True)
class Finding:
    commit: str
    path: str
    line: int
    key: str
    value_length: int
    value_sha256: str


ROTATION_CLASS_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("postgresql", re.compile(r"(POSTGRES|DATABASE_URL)", re.IGNORECASE)),
    ("redis", re.compile(r"(REDIS)", re.IGNORECASE)),
    ("jwt", re.compile(r"(JWT)", re.IGNORECASE)),
    ("model_api", re.compile(r"(OPENAI|ANTHROPIC|GEMINI|API_KEY)", re.IGNORECASE)),
    ("acceptance_users", re.compile(r"(RESEARCHER|GOV|INDUSTRY).*PASSWORD", re.IGNORECASE)),
)


def run_git(repo: Path, args: list[str]) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def normalize_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1].strip()
    return value


def is_secret_assignment(line: str) -> tuple[str, str] | None:
    match = ASSIGNMENT_RE.match(line)
    if not match:
        return None

    key, raw_value = match.groups()
    value = normalize_value(raw_value)
    if not value or PLACEHOLDER_RE.fullmatch(value):
        return None
    if not SECRET_KEY_RE.search(key):
        return None
    return key, value


def runtime_paths_in_commit(repo: Path, commit: str, basenames: set[str]) -> list[str]:
    names = run_git(repo, ["ls-tree", "-r", "--name-only", commit]).splitlines()
    return sorted(name for name in names if Path(name).name in basenames)


def commits_touching_env_history(repo: Path, basenames: Iterable[str]) -> list[str]:
    pathspecs = list(basenames)
    output = run_git(repo, ["log", "--all", "--full-history", "--format=%H", "--", *pathspecs])
    commits: list[str] = []
    seen: set[str] = set()
    for line in output.splitlines():
        commit = line.strip()
        if commit and commit not in seen:
            seen.add(commit)
            commits.append(commit)
    return commits


def scan_history(repo: Path, basenames: Iterable[str]) -> tuple[list[Finding], int, int]:
    basename_set = set(basenames)
    commits = commits_touching_env_history(repo, basename_set)
    findings: list[Finding] = []
    file_versions = 0

    for commit in commits:
        for path in runtime_paths_in_commit(repo, commit, basename_set):
            file_versions += 1
            try:
                content = run_git(repo, ["show", f"{commit}:{path}"])
            except RuntimeError:
                continue
            for line_number, line in enumerate(content.splitlines(), start=1):
                result = is_secret_assignment(line)
                if not result:
                    continue
                key, value = result
                findings.append(
                    Finding(
                        commit=commit,
                        path=path,
                        line=line_number,
                        key=key,
                        value_length=len(value),
                        value_sha256=hashlib.sha256(value.encode("utf-8")).hexdigest()[:12],
                    )
                )
    return findings, len(commits), file_versions


def write_json(path: Path, findings: list[Finding], commits_scanned: int, file_versions: int) -> None:
    payload = {
        "status": "FAIL" if findings else "PASS",
        "commits_scanned": commits_scanned,
        "file_versions_scanned": file_versions,
        "finding_count": len(findings),
        "key_counts": dict(sorted(Counter(f.key for f in findings).items())),
        "remediation": build_remediation_summary(findings, commits_scanned, file_versions),
        "findings": [dataclasses.asdict(finding) for finding in findings],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def rotation_classes_for_key(key: str) -> list[str]:
    classes = [name for name, pattern in ROTATION_CLASS_PATTERNS if pattern.search(key)]
    return classes or ["unknown_secret"]


def build_remediation_summary(
    findings: list[Finding],
    commits_scanned: int,
    file_versions: int,
) -> dict[str, object]:
    affected_paths = sorted({finding.path for finding in findings})
    affected_keys = sorted({finding.key for finding in findings})
    unique_fingerprints = sorted({f"{finding.key}:{finding.value_sha256}" for finding in findings})
    rotation_classes = sorted(
        {
            rotation_class
            for key in affected_keys
            for rotation_class in rotation_classes_for_key(key)
        }
    )
    filter_repo_args = [item for path in affected_paths for item in ("--path", path)]

    required_actions: list[str] = []
    if findings:
        required_actions = [
            "freeze repository writes and branch automation",
            "rotate all affected credential classes before unfreezing writes",
            "rewrite runtime environment-file history in an approved mirror clone",
            "force-push rewritten refs only after repository-owner approval",
            "require contributors and CI runners to re-clone or drop stale refs",
            "rerun this scanner on the rewritten history and require zero findings",
        ]

    return {
        "status": "FAIL" if findings else "PASS",
        "commits_scanned": commits_scanned,
        "file_versions_scanned": file_versions,
        "finding_count": len(findings),
        "unique_secret_fingerprint_count": len(unique_fingerprints),
        "affected_paths": affected_paths,
        "affected_keys": affected_keys,
        "rotation_classes": rotation_classes,
        "filter_repo_args": filter_repo_args,
        "required_actions": required_actions,
    }


def print_text(findings: list[Finding], commits_scanned: int, file_versions: int, max_findings: int) -> None:
    status = "FAIL" if findings else "PASS"
    print(f"S3-09 env history scan: {status}")
    print(f"commits scanned: {commits_scanned}")
    print(f"runtime env file versions scanned: {file_versions}")
    print(f"secret-like assignments: {len(findings)}")

    if not findings:
        return

    print("key counts:")
    for key, count in Counter(f.key for f in findings).most_common():
        print(f"  {key}: {count}")

    print(f"sample findings, first {min(max_findings, len(findings))}:")
    for finding in findings[:max_findings]:
        print(
            f"  {finding.commit[:12]} {finding.path}:{finding.line} "
            f"{finding.key} len={finding.value_length} sha256={finding.value_sha256}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository path")
    parser.add_argument(
        "--env-file",
        action="append",
        dest="env_files",
        help="Runtime env basename to scan; repeatable. Defaults to known runtime env names.",
    )
    parser.add_argument("--json-output", type=Path, help="Write full redacted JSON findings")
    parser.add_argument("--max-findings", type=int, default=50, help="Max text sample findings")
    parser.add_argument(
        "--allow-findings",
        action="store_true",
        help="Exit 0 even when findings are present",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo = args.repo.resolve()
    basenames = tuple(args.env_files or RUNTIME_ENV_BASENAMES)

    findings, commits_scanned, file_versions = scan_history(repo, basenames)
    print_text(findings, commits_scanned, file_versions, args.max_findings)
    if args.json_output:
        write_json(args.json_output, findings, commits_scanned, file_versions)
    return 0 if args.allow_findings or not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

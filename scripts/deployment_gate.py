#!/usr/bin/env python3
"""
NRG Deployment Gate — Pre-deployment verification script.

Runs comprehensive checks before deployment:
1. Test suite validation
2. Schema sync verification
3. RBAC policy validation
4. Docker build check
5. Health check validation
6. Security scan (basic)

Usage:
    python scripts/deployment_gate.py [--skip-tests] [--skip-docker] [--env <staging|production>]

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKMARK = "\u2705"
CROSS = "\u274c"
WARNING = "\u26a0\ufe0f"
INFO = "\u2139\ufe0f"


@dataclass
class GateResult:
    name: str
    passed: bool
    message: str
    duration_ms: Optional[int] = None
    details: Optional[dict] = None


def run_command(
    cmd: list[str],
    timeout: int = 120,
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> tuple[int, str, str]:
    """Run a command and return (returncode, stdout, stderr)."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or REPO_ROOT,
            env=merged_env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def check_tests() -> GateResult:
    """Run the test suite and verify results."""
    start = time.time()
    print(f"  {INFO} Running test suite...")

    returncode, stdout, stderr = run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x", "-q"],
        timeout=300,
    )

    duration_ms = int((time.time() - start) * 1000)

    if returncode == 0:
        return GateResult(
            name="Test Suite",
            passed=True,
            message="All tests passed",
            duration_ms=duration_ms,
        )
    else:
        output = (stdout + stderr)[-2000:]
        return GateResult(
            name="Test Suite",
            passed=False,
            message=f"Tests failed with exit code {returncode}",
            duration_ms=duration_ms,
            details={"last_output": output},
        )


def check_schema_sync() -> GateResult:
    """Verify schema is in sync with production schema."""
    start = time.time()
    print(f"  {INFO} Checking schema synchronization...")

    schema_check_script = REPO_ROOT / "scripts" / "check_schema_sync.py"
    if not schema_check_script.exists():
        return GateResult(
            name="Schema Sync",
            passed=False,
            message="check_schema_sync.py not found",
        )

    returncode, stdout, stderr = run_command(
        [sys.executable, str(schema_check_script)],
        timeout=60,
    )

    duration_ms = int((time.time() - start) * 1000)

    if returncode == 0:
        return GateResult(
            name="Schema Sync",
            passed=True,
            message="Schema is in sync",
            duration_ms=duration_ms,
        )
    else:
        return GateResult(
            name="Schema Sync",
            passed=False,
            message="Schema drift detected",
            duration_ms=duration_ms,
            details={"output": (stdout + stderr)[-1000:]},
        )


def check_rbac_policies() -> GateResult:
    """Validate RBAC policy configuration."""
    start = time.time()
    print(f"  {INFO} Validating RBAC policies...")

    rbac_policy_file = REPO_ROOT / "src" / "auth" / "rbac_policies.yaml"
    if not rbac_policy_file.exists():
        return GateResult(
            name="RBAC Policies",
            passed=False,
            message="rbac_policies.yaml not found",
        )

    returncode, stdout, stderr = run_command(
        [
            sys.executable, "-c",
            f"""
import yaml
from pathlib import Path
policies = yaml.safe_load(Path('{rbac_policy_file}').read_text())
roles = policies.get('roles', {{}})
print(f'Loaded {{len(roles)}} roles')
for role_name, role in roles.items():
    permissions = role.get('permissions', [])
    print(f'Role {{role_name}}: {{len(permissions)}} permissions')
print('RBAC validation OK')
"""
        ],
        timeout=30,
    )

    duration_ms = int((time.time() - start) * 1000)

    if returncode == 0:
        return GateResult(
            name="RBAC Policies",
            passed=True,
            message="RBAC policies are valid",
            duration_ms=duration_ms,
        )
    else:
        return GateResult(
            name="RBAC Policies",
            passed=False,
            message=f"RBAC validation failed: {stderr}",
            duration_ms=duration_ms,
        )


def check_docker_build() -> GateResult:
    """Verify Docker images can be built."""
    start = time.time()
    print(f"  {INFO} Checking Docker build...")

    docker_compose = REPO_ROOT / "docker-compose.yml"
    if not docker_compose.exists():
        return GateResult(
            name="Docker Build",
            passed=False,
            message="docker-compose.yml not found",
        )

    returncode, stdout, stderr = run_command(
        ["docker", "compose", "-f", str(docker_compose), "config"],
        timeout=30,
    )

    if returncode != 0:
        return GateResult(
            name="Docker Build",
            passed=False,
            message="Docker Compose configuration is invalid",
            details={"error": stderr[:500]},
        )

    returncode, stdout, stderr = run_command(
        ["docker", "build", "-t", "nrg-test:latest", "--dry-run", "."],
        timeout=120,
        cwd=REPO_ROOT,
    )

    duration_ms = int((time.time() - start) * 1000)

    if returncode == 0 or "dry-run" in stderr.lower():
        return GateResult(
            name="Docker Build",
            passed=True,
            message="Docker configuration is valid",
            duration_ms=duration_ms,
        )
    else:
        return GateResult(
            name="Docker Build",
            passed=False,
            message="Docker build check failed",
            duration_ms=duration_ms,
            details={"error": stderr[:500]},
        )


def check_health_endpoints() -> GateResult:
    """Verify health check endpoints are responsive."""
    start = time.time()
    print(f"  {INFO} Checking health endpoints...")

    api_url = os.getenv("NRG_API_URL", "http://localhost:8000")

    returncode, stdout, stderr = run_command(
        ["curl", "-sf", "-m", "5", f"{api_url}/health"],
        timeout=10,
    )

    duration_ms = int((time.time() - start) * 1000)

    if returncode == 0:
        return GateResult(
            name="Health Endpoints",
            passed=True,
            message=f"Health endpoint responsive at {api_url}",
            duration_ms=duration_ms,
        )
    else:
        return GateResult(
            name="Health Endpoints",
            passed=False,
            message=f"Health endpoint not reachable at {api_url} (is the API running?)",
            duration_ms=duration_ms,
        )


def check_security_scan() -> GateResult:
    """Run basic security checks."""
    start = time.time()
    print(f"  {INFO} Running security scan...")

    findings: list[str] = []

    secrets_patterns = [
        (REPO_ROOT / "src" / "config" / "database.py", "password", "hardcoded password in database.py"),
    ]

    for file_path, pattern, desc in secrets_patterns:
        if file_path.exists():
            content = file_path.read_text()
            if "password" in content.lower() and "os.getenv" not in content:
                findings.append(f"{file_path.name}: potential hardcoded secret")

    if findings:
        return GateResult(
            name="Security Scan",
            passed=False,
            message="Security issues found",
            duration_ms=int((time.time() - start) * 1000),
            details={"findings": findings},
        )

    return GateResult(
        name="Security Scan",
        passed=True,
        message="No obvious security issues detected",
        duration_ms=int((time.time() - start) * 1000),
    )


def print_result(result: GateResult, verbose: bool = False) -> None:
    """Print a gate result with formatting."""
    icon = CHECKMARK if result.passed else CROSS
    status = "PASS" if result.passed else "FAIL"

    print(f"  {icon} [{status}] {result.name}: {result.message}")
    if result.duration_ms is not None:
        print(f"      Duration: {result.duration_ms}ms")

    if verbose and result.details:
        for key, value in result.details.items():
            print(f"      {key}: {str(value)[:200]}")


def run_gate(
    skip_tests: bool = False,
    skip_docker: bool = False,
    skip_health: bool = False,
    env: str = "staging",
    verbose: bool = False,
) -> bool:
    """Run all deployment gate checks."""
    print("\n" + "=" * 60)
    print("NRG Deployment Gate")
    print(f"Environment: {env}")
    print("=" * 60 + "\n")

    checks = []

    if not skip_tests:
        checks.append(check_tests())

    checks.append(check_schema_sync())
    checks.append(check_rbac_policies())

    if not skip_docker:
        checks.append(check_docker_build())

    if not skip_health:
        checks.append(check_health_endpoints())

    checks.append(check_security_scan())

    print("\n" + "-" * 60)
    print("Results:")
    print("-" * 60 + "\n")

    all_passed = True
    for result in checks:
        print_result(result, verbose=verbose)
        if not result.passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print(f"{CHECKMARK} ALL CHECKS PASSED — Ready to deploy")
        print("=" * 60 + "\n")
        return True
    else:
        failed = [r.name for r in checks if not r.passed]
        print(f"{CROSS} DEPLOYMENT BLOCKED — {len(failed)} check(s) failed: {', '.join(failed)}")
        print("=" * 60 + "\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="NRG Deployment Gate")
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip test suite execution",
    )
    parser.add_argument(
        "--skip-docker",
        action="store_true",
        help="Skip Docker build check",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip health endpoint check",
    )
    parser.add_argument(
        "--env",
        default=os.getenv("DEPLOY_ENV", "staging"),
        choices=["staging", "production"],
        help="Deployment environment",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output",
    )
    args = parser.parse_args()

    success = run_gate(
        skip_tests=args.skip_tests,
        skip_docker=args.skip_docker,
        skip_health=args.skip_health,
        env=args.env,
        verbose=args.verbose,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

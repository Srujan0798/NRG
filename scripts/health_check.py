#!/usr/bin/env python3
"""
Enhanced Health Check Script for National Research Graph
Validates all system components are operational.
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return {
            "status": "PASS",
            "version": f"{version.major}.{version.minor}.{version.micro}",
        }
    return {
        "status": "FAIL",
        "version": f"{version.major}.{version.minor}.{version.micro}",
    }


def check_dependencies():
    """Check required Python packages."""
    required = ["pytest", "requests"]
    results = {}

    for package in required:
        try:
            __import__(package.replace("-", "_"))
            results[package] = "INSTALLED"
        except ImportError:
            results[package] = "MISSING"

    all_installed = all(v == "INSTALLED" for v in results.values())
    return {"status": "PASS" if all_installed else "FAIL", "packages": results}


def check_project_structure():
    """Check project directory structure."""
    required_dirs = ["src", "tests", "scripts", "docs", "frontend"]
    results = {}

    for dir_name in required_dirs:
        path = Path(dir_name)
        results[dir_name] = "EXISTS" if path.exists() else "MISSING"

    all_exist = all(v == "EXISTS" for v in results.values())
    return {"status": "PASS" if all_exist else "FAIL", "directories": results}


def check_security_module():
    """Check security module is functional."""
    try:
        from src.security.gateway.prompt_sanitiser import PromptSanitiser

        sanitiser = PromptSanitiser()

        aadhaar_result = sanitiser.detect_pii("1234-5678-9012")
        pan_result = sanitiser.detect_pii("ABCDE1234F")
        phone_result = sanitiser.detect_pii("9876543210")

        tests = {
            "aadhaar_detection": aadhaar_result == "aadhaar",
            "pan_detection": pan_result == "pan",
            "phone_detection": phone_result == "phone",
        }

        all_pass = all(tests.values())
        return {"status": "PASS" if all_pass else "FAIL", "tests": tests}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def check_rbac_module():
    """Check RBAC module is functional."""
    try:
        from src.security.rbac.middleware import RBACMiddleware

        middleware = RBACMiddleware()

        tier1 = middleware.get_allowed_tiers("researcher")
        tier2 = middleware.get_allowed_tiers("government")
        tier3 = middleware.get_allowed_tiers("industry")

        tests = {
            "tier1_access": tier1 == [1, 2, 3],
            "tier2_access": tier2 == [2, 3],
            "tier3_access": tier3 == [3],
        }

        all_pass = all(tests.values())
        return {"status": "PASS" if all_pass else "FAIL", "tests": tests}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def check_python_modules():
    """Check Python modules are importable."""
    try:
        from src.orchestration.graph import NRGWorkflow

        return {"status": "PASS", "modules": ["NRGWorkflow"]}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


def run_health_check():
    """Run all health checks and generate report."""
    print("=" * 60)
    print("NATIONAL RESEARCH GRAPH - HEALTH CHECK")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "Project Structure": check_project_structure(),
        "Security Module": check_security_module(),
        "RBAC Module": check_rbac_module(),
        "Python Modules": check_python_modules(),
    }

    all_passed = True
    for name, result in checks.items():
        status = result.get("status", "UNKNOWN")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {name}: {status}")

        if "packages" in result:
            for pkg, st in result["packages"].items():
                print(f"   - {pkg}: {st}")

        if "directories" in result:
            for dir_name, st in result["directories"].items():
                print(f"   - {dir_name}: {st}")

        if "tests" in result:
            for test_name, test_result in result["tests"].items():
                test_icon = "✓" if test_result else "✗"
                print(f"   - {test_name}: {test_icon}")

        if result.get("status") != "PASS":
            all_passed = False

    print()
    print("=" * 60)
    print(
        f"OVERALL STATUS: {'✅ ALL CHECKS PASSED' if all_passed else '⚠️ SOME CHECKS FAILED'}"
    )
    print("=" * 60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "PASS" if all_passed else "FAIL",
        "checks": checks,
    }

    report_path = Path(".protocol/state/health_check_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nReport saved to: {report_path}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_health_check())

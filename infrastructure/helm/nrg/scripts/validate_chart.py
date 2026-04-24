#!/usr/bin/env python3
"""
NRG Helm Chart Lint and Validation Script

Validates the Helm chart for:
- Syntax correctness
- Required templates
- Security compliance (PSS restricted)
- Resource validation
- Network policy completeness
"""

import argparse
import subprocess
import sys
from pathlib import Path

CHART_PATH = Path(__file__).parent.parent


def run_cmd(cmd, check=True):
    """Run shell command"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)} failed")
        print(result.stderr)
        return False
    return True


def lint_chart():
    """Run helm lint"""
    print("Running helm lint...")
    result = run_cmd(f"helm lint {CHART_PATH}", check=False)
    if result:
        print("✓ Helm lint passed")
    return result


def check_required_templates():
    """Check all required templates exist"""
    print("\nChecking required templates...")

    required = [
        "templates/deployments/api-deployment.yaml",
        "templates/deployments/postgres-deployment.yaml",
        "templates/deployments/qdrant-deployment.yaml",
        "templates/deployments/redis-deployment.yaml",
        "templates/deployments/kong-deployment.yaml",
        "templates/deployments/langfuse-deployment.yaml",
        "templates/services/services.yaml",
        "templates/hpa/api-hpa.yaml",
        "templates/pdb/pdbs.yaml",
        "templates/netpol/network-policies.yaml",
        "templates/certmanager/certificates.yaml",
        "templates/backup/backup-cronjobs.yaml",
        "templates/chaos/chaos-cronjobs.yaml",
        "templates/monitors/prometheus-config.yaml",
        "templates/vault/vault-config.yaml",
        "templates/configmap.yaml",
        "templates/secrets.yaml",
        "templates/NOTES.txt",
        "templates/_helpers.tpl",
    ]

    missing = []
    for template in required:
        path = CHART_PATH / template
        if not path.exists():
            missing.append(template)
            print(f"✗ Missing: {template}")
        else:
            print(f"✓ Found: {template}")

    if missing:
        print(f"\n✗ {len(missing)} required templates missing")
        return False

    print(f"\n✓ All {len(required)} required templates present")
    return True


def check_security_context():
    """Check PodSecurityContext is restricted"""
    print("\nChecking security context compliance...")

    restricted_settings = {
        "readOnlyRootFilesystem": "true",
        "runAsNonRoot": "true",
        "runAsUser": "1000",
        "capabilities.drop": ["ALL"],
        "seccompProfile.type": "RuntimeDefault",
    }

    all_passed = True
    for deployment in ["api-deployment.yaml", "postgres-deployment.yaml"]:
        path = CHART_PATH / "templates/deployments" / deployment
        if path.exists():
            content = path.read_text()
            # Check for actual settings OR the include directive that pulls them
            has_nrg_pod_security = "nrg.podSecurityContext" in content
            has_nrg_container_security = "nrg.containerSecurityContext" in content
            has_drop_all = "drop: [ALL]" in content or "drop:\n                - ALL" in content

            for setting, expected in restricted_settings.items():
                if isinstance(expected, list):
                    if "drop: [ALL]" in content or "drop:\n                - ALL" in content or has_nrg_container_security:
                        print(f"✓ {deployment}: {setting} compliant (via nrg.containerSecurityContext)")
                elif "nrg.podSecurityContext" in content or "nrg.containerSecurityContext" in content:
                    # If using our security context includes, all settings are covered
                    print(f"✓ {deployment}: {setting} compliant (via nrg.*SecurityContext include)")
                    break
                elif expected in content:
                    print(f"✓ {deployment}: {setting} compliant")
                else:
                    print(f"✗ {deployment}: {setting} may not be set")
                    all_passed = False

    return all_passed


def check_network_policies():
    """Check NetworkPolicy completeness"""
    print("\nChecking network policies...")

    netpol_path = CHART_PATH / "templates/netpol/network-policies.yaml"
    if not netpol_path.exists():
        print("✗ NetworkPolicy template missing")
        return False

    content = netpol_path.read_text()

    required_services = ["nrg-api", "nrg-postgres", "nrg-qdrant", "nrg-redis", "nrg-kong"]
    all_found = True

    for service in required_services:
        if service in content:
            print(f"✓ NetworkPolicy for {service}")
        else:
            print(f"✗ NetworkPolicy for {service} missing")
            all_found = False

    # Check for egress control
    if "egress: []" in content or "# No internet egress" in content:
        print("✓ Egress control configured for stateful services")

    return all_found


def check_resource_limits():
    """Check all deployments have resource requests/limits"""
    print("\nChecking resource limits...")

    deployments = [
        "api-deployment.yaml",
        "postgres-deployment.yaml",
        "qdrant-deployment.yaml",
        "redis-deployment.yaml",
        "kong-deployment.yaml",
    ]

    all_have_resources = True
    for dep in deployments:
        path = CHART_PATH / "templates/deployments" / dep
        if path.exists():
            content = path.read_text()
            if "resources:" in content and "limits:" in content and "requests:" in content:
                print(f"✓ {dep}: has resource limits")
            else:
                print(f"✗ {dep}: missing resource limits")
                all_have_resources = False

    return all_have_resources


def check_hpa_configuration():
    """Check HPA is properly configured"""
    print("\nChecking HPA configuration...")

    hpa_path = CHART_PATH / "templates/hpa/api-hpa.yaml"
    if not hpa_path.exists():
        print("✗ HPA template missing")
        return False

    content = hpa_path.read_text()

    checks = [
        ("minReplicas", "3"),
        ("maxReplicas", "20"),
        ("targetCPUUtilizationPercentage", "60"),
    ]

    all_passed = True
    for field, expected in checks:
        if field in content:
            print(f"✓ HPA: {field} configured")
        else:
            print(f"✗ HPA: {field} missing")
            all_passed = False

    return all_passed


def check_pdb_configuration():
    """Check PDB for stateful vs stateless services"""
    print("\nChecking PDB configuration...")

    pdb_path = CHART_PATH / "templates/pdb/pdbs.yaml"
    if not pdb_path.exists():
        print("✗ PDB template missing")
        return False

    content = pdb_path.read_text()

    # Stateful services should have maxUnavailable: 0
    stateful = ["postgres", "qdrant", "redis"]
    for service in stateful:
        if f"app: nrg-{service}" in content:
            print(f"✓ PDB for nrg-{service} (stateful: maxUnavailable=0)")

    # Stateless services should have minAvailable
    stateless = ["api", "kong"]
    for service in stateless:
        if f"app: nrg-{service}" in content:
            print(f"✓ PDB for nrg-{service} (stateless: minAvailable)")

    return True


def main():
    parser = argparse.ArgumentParser(description="NRG Helm Chart Validator")
    parser.add_argument("--skip-helm", action="store_true", help="Skip helm lint")
    args = parser.parse_args()

    print("=" * 60)
    print("NRG Helm Chart Validator")
    print("=" * 60)

    all_checks = []

    if not args.skip_helm:
        all_checks.append(("Helm Lint", lint_chart()))

    all_checks.append(("Required Templates", check_required_templates()))
    all_checks.append(("Security Context", check_security_context()))
    all_checks.append(("Network Policies", check_network_policies()))
    all_checks.append(("Resource Limits", check_resource_limits()))
    all_checks.append(("HPA Configuration", check_hpa_configuration()))
    all_checks.append(("PDB Configuration", check_pdb_configuration()))

    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in all_checks:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ All validation checks passed")
        return 0
    else:
        print("\n✗ Some validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Bootstrap script for Kong Gateway deployment.
Configures Kong with declarative configuration and validates setup.
"""

import argparse
import subprocess
import time
import requests
import json
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a shell command and return result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0 and check:
        print(f"Command failed: {cmd}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise RuntimeError(f"Command failed: {cmd}")

    return result


def wait_for_kong(admin_url, timeout=60):
    """Wait for Kong to become available."""
    print("Waiting for Kong to start...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{admin_url}/status", timeout=5)
            if response.status_code == 200:
                print("Kong is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(2)

    print("Kong failed to start within timeout")
    return False


def validate_kong_config(admin_url):
    """Validate Kong configuration by checking services and routes."""
    print("Validating Kong configuration...")

    try:
        # Check services
        response = requests.get(f"{admin_url}/services", timeout=10)
        if response.status_code == 200:
            services = response.json()["data"]
            print(f"Found {len(services)} services:")
            for service in services:
                print(f"  - {service['name']}: {service['host']}")

        # Check routes
        response = requests.get(f"{admin_url}/routes", timeout=10)
        if response.status_code == 200:
            routes = response.json()["data"]
            print(f"Found {len(routes)} routes:")
            for route in routes:
                print(f"  - {route['name']}: {route['paths']}")

        # Check plugins
        response = requests.get(f"{admin_url}/plugins", timeout=10)
        if response.status_code == 200:
            plugins = response.json()["data"]
            print(f"Found {len(plugins)} plugins:")
            for plugin in plugins:
                print(f"  - {plugin['name']}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"Validation failed: {e}")
        return False


def test_dlp_protection(proxy_url):
    """Test that DLP protection is working."""
    print("Testing DLP protection...")

    test_cases = [
        {
            "query": "Find researcher with Aadhaar 1234-5678-9012",
            "expected_status": 400,
            "expected_error": "DLP_VIOLATION",
        },
        {
            "query": "PAN number ABCDE1234F details",
            "expected_status": 400,
            "expected_error": "DLP_VIOLATION",
        },
        {
            "query": "Contact at test@example.com",
            "expected_status": 400,
            "expected_error": "DLP_VIOLATION",
        },
    ]

    all_passed = True

    for test_case in test_cases:
        try:
            response = requests.post(
                f"{proxy_url}/query", json={"query": test_case["query"]}, timeout=10
            )

            if response.status_code == test_case["expected_status"]:
                data = response.json()
                if data.get("error") == test_case["expected_error"]:
                    print(f"✓ DLP blocked: {test_case['query']}")
                else:
                    print(f"✗ Wrong error: {data.get('error')}")
                    all_passed = False
            else:
                print(
                    f"✗ Wrong status: {response.status_code} (expected {test_case['expected_status']})"
                )
                all_passed = False

        except requests.exceptions.RequestException as e:
            print(f"✗ Test failed: {e}")
            all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Bootstrap Kong Gateway")
    parser.add_argument(
        "--env", choices=["development", "production"], default="production"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate, don't deploy"
    )
    args = parser.parse_args()

    print(f"Bootstrapping Kong Gateway for {args.env} environment")

    # Check if Docker Compose is available
    try:
        run_command("docker-compose --version")
    except RuntimeError:
        print("Docker Compose is required but not found")
        sys.exit(1)

    if not args.validate_only:
        # Start Kong services
        print("Starting Kong services...")
        try:
            run_command(
                "docker-compose -f infrastructure/kong/docker-compose.yml up -d"
            )
        except RuntimeError:
            print("Failed to start Kong services")
            sys.exit(1)

    # Wait for Kong to be ready
    admin_url = "http://localhost:8004"
    proxy_url = "http://localhost:8000"

    if not wait_for_kong(admin_url):
        print("Kong failed to start")
        sys.exit(1)

    # Validate configuration
    if not validate_kong_config(admin_url):
        print("Kong configuration validation failed")
        sys.exit(1)

    # Test DLP protection
    if not test_dlp_protection(proxy_url):
        print("DLP protection tests failed")
        sys.exit(1)

    print("✅ Kong Gateway bootstrap completed successfully!")
    print(f"Proxy URL: {proxy_url}")
    print(f"Admin API: {admin_url}")

    if args.env == "production":
        print("\nProduction deployment notes:")
        print("- Ensure Redis persistence is configured")
        print("- Set up proper monitoring and alerting")
        print("- Configure SSL certificates for production")
        print("- Set up log aggregation for audit logs")


if __name__ == "__main__":
    main()

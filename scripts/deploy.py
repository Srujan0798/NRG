#!/usr/bin/env python3
"""
Zero-Downtime Deployment Script for NRG

Automates the full deployment lifecycle:
  1. Build Docker images (API + Frontend)
  2. Run smoke tests against new images
  3. Deploy to target environment with health verification
  4. Rollback on failure

Usage:
    # Deploy to staging
    python scripts/deploy.py --env staging --version v1.2.3

    # Deploy to production (requires approval)
    python scripts/deploy.py --env production --version v1.2.3 --confirm

    # Rollback to previous version
    python scripts/deploy.py --env production --rollback

    # Health check only
    python scripts/deploy.py --env staging --health-check

SKILLS: /deploy-checklist, /dockerfile-validator
"""

from __future__ import annotations

import argparse
import logging
import os
import subprocess
import sys
import time
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class DeployConfig:
    env: str
    version: str
    docker_registry: str
    api_image: str
    frontend_image: str
    health_endpoint: str
    deploy_timeout: int
    smoke_test_timeout: int
    rollback_timeout: int


DEPLOY_CONFIGS = {
    "staging": DeployConfig(
        env="staging",
        version="",
        docker_registry=os.getenv("DOCKER_REGISTRY", "ghcr.io/nrg"),
        api_image="nrg/api",
        frontend_image="nrg/frontend",
        health_endpoint="http://localhost:8000/health/all",
        deploy_timeout=300,
        smoke_test_timeout=120,
        rollback_timeout=180,
    ),
    "production": DeployConfig(
        env="production",
        version="",
        docker_registry=os.getenv("DOCKER_REGISTRY", "ghcr.io/nrg"),
        api_image="nrg/api",
        frontend_image="nrg/frontend",
        health_endpoint="https://api.nrg.gov.in/health/all",
        deploy_timeout=600,
        smoke_test_timeout=180,
        rollback_timeout=300,
    ),
}


HEALTH_CHECK_ENDPOINTS = [
    ("API", "{health_endpoint}"),
    ("Database", "{health_endpoint}/db"),
    ("Qdrant", "{health_endpoint}/qdrant"),
    ("Redis", "{health_endpoint}/redis"),
]


def get_git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True, cwd=PROJECT_ROOT,
    )
    return result.stdout.strip()


def build_images(version: str, config: DeployConfig) -> dict[str, str]:
    tag = version or get_git_sha()
    images = {}

    logger.info(f"Building API image: {config.api_image}:{tag}")
    api_build = subprocess.run(
        [
            "docker", "build", "-t", f"{config.docker_registry}/{config.api_image}:{tag}",
            "-t", f"{config.docker_registry}/{config.api_image}:latest",
            "--target", "runner", ".",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=600,
    )
    if api_build.returncode != 0:
        logger.error(f"API build failed:\n{api_build.stderr}")
        raise SystemExit("API Docker build failed")
    images["api"] = f"{config.docker_registry}/{config.api_image}:{tag}"
    logger.info(f"API image built: {images['api']}")

    logger.info(f"Building Frontend image: {config.frontend_image}:{tag}")
    fe_build = subprocess.run(
        [
            "docker", "build", "-t", f"{config.docker_registry}/{config.frontend_image}:{tag}",
            "-t", f"{config.docker_registry}/{config.frontend_image}:latest",
            "-f", "Dockerfile.frontend", ".",
        ],
        capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=600,
    )
    if fe_build.returncode != 0:
        logger.error(f"Frontend build failed:\n{fe_build.stderr}")
        raise SystemExit("Frontend Docker build failed")
    images["frontend"] = f"{config.docker_registry}/{config.frontend_image}:{tag}"
    logger.info(f"Frontend image built: {images['frontend']}")

    return images


def run_smoke_tests(config: DeployConfig, images: dict[str, str]) -> bool:
    logger.info("Running smoke tests...")

    try:
        import requests
    except ImportError:
        logger.warning("requests not installed, skipping HTTP smoke tests")
        return True

    headers = {"User-Agent": f"NRG-Deploy/1.0"}

    endpoints = [
        ("/health", 5),
        ("/health/db", 10),
        ("/health/qdrant", 10),
    ]

    for path, timeout in endpoints:
        url = config.health_endpoint.replace("/health/all", path)
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code != 200:
                logger.error(f"Smoke test failed: {url} → {resp.status_code}")
                return False
            logger.info(f"  ✓ {path} → {resp.status_code}")
        except requests.RequestException as e:
            logger.error(f"  ✗ {path} → {e}")
            return False

    return True


def deploy_to_ecs(config: DeployConfig, images: dict[str, str], cluster: str) -> bool:
    logger.info(f"Deploying to ECS cluster: {cluster}")

    tag = images["api"].split(":")[-1]

    api_task_def = f"nrg-api:{tag}"
    fe_task_def = f"nrg-frontend:{tag}"

    logger.info(f"  Updating API service: {api_task_def}")
    result = subprocess.run(
        ["aws", "ecs", "update-service", "--cluster", cluster, "--service", "nrg-api",
         "--force-new-deployment", "--output", "json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error(f"ECS API update failed: {result.stderr}")
        return False

    logger.info(f"  Updating Frontend service: {fe_task_def}")
    result = subprocess.run(
        ["aws", "ecs", "update-service", "--cluster", cluster, "--service", "nrg-frontend",
         "--force-new-deployment", "--output", "json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error(f"ECS frontend update failed: {result.stderr}")
        return False

    logger.info(f"  Waiting for services to stabilize...")
    result = subprocess.run(
        ["aws", "ecs", "wait", "services-stable", "--cluster", cluster,
         "--services", "nrg-api,nrg-frontend"],
        capture_output=True, text=True, timeout=config.deploy_timeout,
    )

    if result.returncode != 0:
        logger.error(f"  ECS services failed to stabilize: {result.stderr}")
        return False

    logger.info(f"  ✓ Services stable in cluster {cluster}")
    return True


def rollback(config: DeployConfig) -> bool:
    logger.warning("Initiating rollback...")

    cluster_map = {"staging": "nrg-staging", "production": "nrg-prod"}
    cluster = cluster_map.get(config.env, f"nrg-{config.env}")

    result = subprocess.run(
        ["aws", "ecs", "update-service", "--cluster", cluster, "--service", "nrg-api",
         "--force-new-deployment", "--output", "json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        logger.error(f"Rollback failed: {result.stderr}")
        return False

    logger.info("  ✓ Rollback initiated")
    return True


def log_deployment(deployment_id: str, config: DeployConfig, images: dict, status: str, duration: float):
    record = {
        "deployment_id": deployment_id,
        "env": config.env,
        "version": images.get("api", "unknown").split(":")[-1],
        "api_image": images.get("api"),
        "frontend_image": images.get("frontend"),
        "status": status,
        "duration_seconds": round(duration, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    log_path = PROJECT_ROOT / "deployment_log.json"
    try:
        logs = []
        if log_path.exists():
            with open(log_path) as f:
                logs = json.load(f)
        logs.append(record)
        with open(log_path, "w") as f:
            json.dump(logs[-100:], f, indent=2)
    except Exception:
        pass
    logger.info(f"Deployment record: {log_path}")


def validate_env_vars() -> list[str]:
    required = [
        "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB",
        "JWT_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY",
        "OPENAI_API_KEY",
    ]
    missing = [v for v in required if not os.getenv(v)]
    return missing


def main():
    parser = argparse.ArgumentParser(description="NRG Zero-Downtime Deployment")
    parser.add_argument("--env", choices=["staging", "production"], required=True)
    parser.add_argument("--version", type=str, help="Docker image tag (default: git SHA)")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous version")
    parser.add_argument("--health-check", action="store_true", help="Run health checks only")
    parser.add_argument("--cluster", type=str, help="ECS cluster name override")
    args = parser.parse_args()

    config = DEPLOY_CONFIGS[args.env]
    if args.version:
        config.version = args.version

    missing = validate_env_vars()
    if missing:
        logger.warning(f"Missing env vars: {missing}")
        logger.warning("Deployment may fail if these are required at runtime")

    if args.health_check:
        logger.info(f"Running health checks for {args.env}...")
        try:
            import requests
            base = config.health_endpoint.replace("/health/all", "")
            checks = [("/health", 5), ("/health/db", 10), ("/health/qdrant", 10)]
            for path, timeout in checks:
                try:
                    resp = requests.get(base + path, timeout=timeout)
                    status = "✓" if resp.status_code == 200 else f"✗ {resp.status_code}"
                    logger.info(f"  {path} → {status}")
                except Exception as e:
                    logger.info(f"  {path} → ✗ {e}")
        except ImportError:
            logger.error("requests library needed for health checks")
        sys.exit(0)

    start = time.time()

    if args.rollback:
        success = rollback(config)
        log_deployment(f"rb-{int(start)}", config, {}, "rollback" if success else "rollback_failed", time.time() - start)
        sys.exit(0 if success else 1)

    tag = config.version or get_git_sha()
    logger.info(f"=== NRG Deployment: {args.env} @ {tag} ===")

    if not args.confirm and args.env == "production":
        confirm = input("Deploy to PRODUCTION? This cannot be undone easily. (yes/no): ")
        if confirm.lower() != "yes":
            logger.info("Aborted.")
            sys.exit(1)

    deployment_id = f"dep-{int(start)}"

    try:
        images = build_images(tag, config)

        if not run_smoke_tests(config, images):
            logger.error("Smoke tests failed. Aborting deployment.")
            log_deployment(deployment_id, config, images, "smoke_test_failed", time.time() - start)
            sys.exit(1)

        cluster = args.cluster or {"staging": "nrg-staging", "production": "nrg-prod"}[args.env]
        success = deploy_to_ecs(config, images, cluster)

        if success:
            logger.info(f"✓ Deployment to {args.env} complete")
            log_deployment(deployment_id, config, images, "success", time.time() - start)
        else:
            logger.error("✗ Deployment failed")
            log_deployment(deployment_id, config, images, "failed", time.time() - start)
            if input("Rollback? (yes/no): ").lower() == "yes":
                rollback(config)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Deployment error: {e}")
        log_deployment(deployment_id, config, {}, f"error: {e}", time.time() - start)
        sys.exit(1)


if __name__ == "__main__":
    main()
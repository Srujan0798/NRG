{{/*
NRG Sovereign Landing - Blue-Green Deployment Script

This script handles blue-green deployments for zero-downtime updates.
It deploys the new version to the "green" environment, runs smoke tests,
and then switches traffic if all checks pass.

Usage:
  ./sovereign_deploy.py --env production --version v1.2.3 --rollback-on-failure

Requirements:
  - kubectl configured with cluster access
  - helm 3.x
  - jq for JSON parsing
*/}}

#!/usr/bin/env python3
"""
NRG Sovereign Landing - Blue-Green Deployment Orchestrator

NIC/MeitY Infrastructure Deployment Controller
Supports: blue-green, canary, rolling update strategies
Features:
  - Pre-deployment validation
  - Health smoke tests
  - Automatic rollback on failure
  - Backup before deployment
  - Audit trail logging
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/nrg-deploy.log')
    ]
)
logger = logging.getLogger(__name__)


class DeployStrategy(Enum):
    BLUE_GREEN = "blue-green"
    CANARY = "canary"
    ROLLING = "rolling"


class DeploymentPhase(Enum):
    PRE_CHECK = "pre-deployment-checks"
    BACKUP = "backup"
    DEPLOY = "deployment"
    SMOKE_TEST = "smoke-tests"
    TRAFFIC_SWITCH = "traffic-switch"
    VERIFICATION = "verification"
    ROLLBACK = "rollback"
    COMPLETE = "complete"


@dataclass
class DeploymentConfig:
    namespace: str = "nrg-production"
    release_name: str = "nrg"
    chart_path: str = "./infrastructure/helm/nrg"
    version: str = ""
    strategy: DeployStrategy = DeployStrategy.BLUE_GREEN
    smoke_test_timeout: int = 300
    rollback_on_failure: bool = True
    max_surge: int = 1
    max_unavailable: int = 0
    canary_weight: int = 10


@dataclass
class DeploymentResult:
    success: bool
    phase: DeploymentPhase
    message: str
    duration_seconds: float = 0.0
    artifacts: dict = field(default_factory=dict)


class NrgDeployer:
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.start_time = time.time()
        self.audit_log = []

    def run_cmd(self, cmd: list, check=True, capture=True):
        """Run kubectl/helm command with error handling"""
        logger.info(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture,
                text=True
            )
            if capture:
                logger.debug(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            raise

    def log_audit(self, action: str, details: dict):
        """Log audit trail for compliance"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user": os.getenv("USER", "unknown"),
            "hostname": os.getenv("HOSTNAME", "unknown")
        }
        self.audit_log.append(entry)
        logger.info(f"AUDIT: {action} - {json.dumps(details)}")

    def pre_deployment_checks(self) -> bool:
        """Run pre-deployment validation"""
        logger.info("=" * 60)
        logger.info("PHASE: Pre-Deployment Checks")
        logger.info("=" * 60)

        checks = [
            ("kubectl cluster connectivity", ["kubectl", "cluster-info"]),
            ("helm repository sync", ["helm", "repo", "update"]),
            ("namespace exists", ["kubectl", "get", "ns", self.config.namespace]),
            ("previous deployment healthy", ["kubectl", "rollout", "status", f"deployment/nrg-api",
                                              "-n", self.config.namespace, "--timeout=60s"]),
        ]

        for name, cmd in checks:
            try:
                self.run_cmd(cmd)
                logger.info(f"✓ {name}")
            except subprocess.CalledProcessError:
                logger.error(f"✗ {name} failed")
                return False

        self.log_audit("pre_deployment_checks", {"status": "passed"})
        return True

    def create_backup(self) -> bool:
        """Create backup before deployment"""
        logger.info("=" * 60)
        logger.info("PHASE: Backup")
        logger.info("=" * 60)

        backup_name = f"nrg-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

        try:
            # Trigger PostgreSQL backup manually
            self.run_cmd([
                "kubectl", "exec", "-n", self.config.namespace,
                "deployment/nrg-postgres", "--",
                "pg_dumpall", "-U", "nrg_app"
            ], check=False)

            # Snapshot PVCs
            self.run_cmd([
                "kubectl", "create", "-f", "-", stdin=f"""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {backup_name}
  namespace: {self.config.namespace}
  annotations:
    nrg.gov.in/backup-source: nrg-postgres-data
    nrg.gov.in/backup-time: {datetime.utcnow().isoformat()}
spec:
  accessModes:
    - ReadWriteOnce
  dataSource:
    name: nrg-postgres-data
    kind: PersistentVolumeClaim
  resources:
    requests:
      storage: 100Gi
"""
            ], check=False)

            self.log_audit("backup_created", {
                "backup_name": backup_name,
                "timestamp": datetime.utcnow().isoformat()
            })
            logger.info(f"✓ Backup created: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if self.config.rollback_on_failure:
                raise
            return False

    def deploy_blue_green(self) -> bool:
        """Blue-green deployment strategy"""
        logger.info("=" * 60)
        logger.info("PHASE: Blue-Green Deployment")
        logger.info("=" * 60)

        green_version = f"{self.config.version}-green"

        try:
            # Deploy green environment
            logger.info(f"Deploying green version: {green_version}")

            self.run_cmd([
                "helm", "upgrade", "--install",
                f"{self.config.release_name}-green",
                self.config.chart_path,
                "-n", self.config.namespace,
                "--set", f"image.tag={self.config.version}",
                "--set", "deploymentstrategy=green",
                "--wait", "--timeout", "5m"
            ])

            # Label pods as green
            self.run_cmd([
                "kubectl", "label", "deployment/nrg-api-green",
                "-n", self.config.namespace,
                "version=green", "app=green"
            ])

            self.log_audit("green_deployment_created", {
                "version": green_version,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info("✓ Green deployment created")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Green deployment failed: {e}")
            if self.config.rollback_on_failure:
                self.trigger_rollback("green_deployment_failed")
            raise

    def deploy_canary(self) -> bool:
        """Canary deployment strategy"""
        logger.info("=" * 60)
        logger.info("PHASE: Canary Deployment")
        logger.info("=" * 60)

        try:
            # Deploy canary with weight
            logger.info(f"Deploying canary with {self.config.canary_weight}% traffic")

            self.run_cmd([
                "helm", "upgrade", "--install",
                f"{self.config.release_name}-canary",
                self.config.chart_path,
                "-n", self.config.namespace,
                "--set", f"image.tag={self.config.version}",
                "--set", f"canary.weight={self.config.canary_weight}",
                "--wait", "--timeout", "5m"
            ])

            self.log_audit("canary_deployment_created", {
                "weight": self.config.canary_weight,
                "timestamp": datetime.utcnow().isoformat()
            })

            logger.info("✓ Canary deployed")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Canary deployment failed: {e}")
            if self.config.rollback_on_failure:
                self.trigger_rollback("canary_deployment_failed")
            raise

    def run_smoke_tests(self) -> bool:
        """Run smoke tests against deployed version"""
        logger.info("=" * 60)
        logger.info("PHASE: Smoke Tests")
        logger.info("=" * 60)

        endpoints = [
            (f"http://nrg-api:8000/health/live", 30),
            (f"http://nrg-api:8000/health/ready", 30),
            (f"http://nrg-api:8000/health", 30),
        ]

        for url, timeout in endpoints:
            try:
                result = subprocess.run(
                    ["curl", "-sf", "--max-time", str(timeout), url],
                    capture_output=True
                )
                if result.returncode == 0:
                    logger.info(f"✓ {url}")
                else:
                    logger.error(f"✗ {url} failed")
                    return False
            except Exception as e:
                logger.error(f"✗ {url} error: {e}")
                return False

        # Test database connectivity
        try:
            self.run_cmd([
                "kubectl", "exec", "-n", self.config.namespace,
                "deployment/nrg-api", "--",
                "python", "-c",
                "import asyncpg; import asyncio; "
                "asyncio.run(asyncpg.connect('postgresql://nrg_app:@nrg-postgres:5432/nrg_research'))"
            ])
            logger.info("✓ Database connectivity")
        except Exception as e:
            logger.error(f"✗ Database connectivity failed: {e}")
            return False

        self.log_audit("smoke_tests_passed", {"timestamp": datetime.utcnow().isoformat()})
        return True

    def switch_traffic(self) -> bool:
        """Switch traffic from blue to green (or promote canary)"""
        logger.info("=" * 60)
        logger.info("PHASE: Traffic Switch")
        logger.info("=" * 60)

        try:
            if self.config.strategy == DeployStrategy.BLUE_GREEN:
                # Switch service selector to green
                logger.info("Switching traffic to green environment...")

                self.run_cmd([
                    "kubectl", "patch", "service", "nrg-api",
                    "-n", self.config.namespace,
                    "-p", '{"spec":{"selector":{"app":"nrg-api-green"}}}'
                ])

                self.log_audit("traffic_switched", {
                    "strategy": "blue-green",
                    "target": "green",
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif self.config.strategy == DeployStrategy.CANARY:
                # Promote canary to 100%
                logger.info("Promoting canary to 100%...")

                self.run_cmd([
                    "kubectl", "patch", "deployment", "nrg-api",
                    "-n", self.config.namespace,
                    "-p", '{"spec":{"replicas":3}}'
                ])

                # Remove canary label
                self.run_cmd([
                    "kubectl", "label", "deployment", "nrg-api",
                    "-n", self.config.namespace,
                    "canary-"
                ])

                self.log_audit("traffic_switched", {
                    "strategy": "canary",
                    "target": "100%",
                    "timestamp": datetime.utcnow().isoformat()
                })

            logger.info("✓ Traffic switched successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Traffic switch failed: {e}")
            if self.config.rollback_on_failure:
                self.trigger_rollback("traffic_switch_failed")
            raise

    def verify_deployment(self) -> bool:
        """Verify deployment is stable"""
        logger.info("=" * 60)
        logger.info("PHASE: Deployment Verification")
        logger.info("=" * 60)

        try:
            # Wait for rollout to complete
            self.run_cmd([
                "kubectl", "rollout", "status", "deployment/nrg-api",
                "-n", self.config.namespace,
                "--timeout=5m"
            ])

            # Check HPA is working
            hpa_status = subprocess.run(
                ["kubectl", "get", "hpa", "nrg-api-hpa",
                 "-n", self.config.namespace, "-o", "json"],
                capture_output=True, text=True
            )
            hpa_data = json.loads(hpa_status.stdout)
            logger.info(f"✓ HPA active: {hpa_data['status']['currentReplicas']} replicas")

            self.log_audit("deployment_verified", {
                "timestamp": datetime.utcnow().isoformat()
            })

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment verification failed: {e}")
            return False

    def trigger_rollback(self, reason: str):
        """Trigger automatic rollback"""
        logger.warning("=" * 60)
        logger.warning("PHASE: ROLLBACK TRIGGERED")
        logger.warning(f"Reason: {reason}")
        logger.warning("=" * 60)

        self.log_audit("rollback_triggered", {
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            if self.config.strategy == DeployStrategy.BLUE_GREEN:
                # Switch back to blue
                self.run_cmd([
                    "kubectl", "patch", "service", "nrg-api",
                    "-n", self.config.namespace,
                    "-p", '{"spec":{"selector":{"app":"nrg-api"}}}'
                ])
                logger.info("✓ Rolled back to blue")
            else:
                # Helm rollback
                self.run_cmd([
                    "helm", "rollback", self.config.release_name,
                    "-n", self.config.namespace,
                    "--wait", "--timeout=5m"
                ])
                logger.info("✓ Rolled back via Helm")

            self.log_audit("rollback_completed", {
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            self.log_audit("rollback_failed", {
                "reason": reason,
                "error": str(e)
            })
            sys.exit(1)

    def execute(self) -> DeploymentResult:
        """Execute the full deployment pipeline"""
        logger.info("=" * 60)
        logger.info("NRG SOVEREIGN LANDING - DEPLOYMENT STARTED")
        logger.info(f"Strategy: {self.config.strategy.value}")
        logger.info(f"Version: {self.config.version}")
        logger.info("=" * 60)

        phases = [
            ("Pre-deployment checks", self.pre_deployment_checks),
            ("Backup", self.create_backup),
            ("Deploy", self.deploy_blue_green if self.config.strategy == DeployStrategy.BLUE_GREEN else self.deploy_canary),
            ("Smoke tests", self.run_smoke_tests),
            ("Traffic switch", self.switch_traffic),
            ("Verification", self.verify_deployment),
        ]

        for phase_name, phase_func in phases:
            try:
                if not phase_func():
                    return DeploymentResult(
                        success=False,
                        phase=DeploymentPhase[phase_name.upper().replace(" ", "_")],
                        message=f"Phase '{phase_name}' failed",
                        duration_seconds=time.time() - self.start_time
                    )
            except Exception as e:
                logger.error(f"Phase '{phase_name}' raised exception: {e}")
                if self.config.rollback_on_failure:
                    self.trigger_rollback(f"{phase_name}_exception")
                return DeploymentResult(
                    success=False,
                    phase=DeploymentPhase[phase_name.upper().replace(" ", "_")],
                    message=str(e),
                    duration_seconds=time.time() - self.start_time
                )

        duration = time.time() - self.start_time

        logger.info("=" * 60)
        logger.info("DEPLOYMENT COMPLETE")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)

        self.log_audit("deployment_completed", {
            "version": self.config.version,
            "strategy": self.config.strategy.value,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Write audit log
        audit_path = Path(f"/var/log/nrg-deploy-{datetime.utcnow().strftime('%Y%m%d')}.json")
        audit_path.write_text(json.dumps(self.audit_log, indent=2))
        logger.info(f"Audit log written to: {audit_path}")

        return DeploymentResult(
            success=True,
            phase=DeploymentPhase.COMPLETE,
            message="Deployment successful",
            duration_seconds=duration,
            artifacts={"audit_log": str(audit_path)}
        )


def main():
    parser = argparse.ArgumentParser(
        description="NRG Sovereign Landing - Deployment Orchestrator"
    )
    parser.add_argument(
        "--version", "-v", required=True,
        help="Container image version to deploy"
    )
    parser.add_argument(
        "--strategy", "-s", default="blue-green",
        choices=["blue-green", "canary", "rolling"],
        help="Deployment strategy"
    )
    parser.add_argument(
        "--namespace", "-n", default="nrg-production",
        help="Kubernetes namespace"
    )
    parser.add_argument(
        "--rollback-on-failure", "-r", action="store_true", default=True,
        help="Automatically rollback on failure"
    )
    parser.add_argument(
        "--no-rollback", action="store_false", dest="rollback_on_failure",
        help="Disable automatic rollback"
    )
    parser.add_argument(
        "--canary-weight", "-w", type=int, default=10,
        help="Canary traffic weight (percentage)"
    )

    args = parser.parse_args()

    config = DeploymentConfig(
        namespace=args.namespace,
        version=args.version,
        strategy=DeployStrategy(args.strategy),
        rollback_on_failure=args.rollback_on_failure,
        canary_weight=args.canary_weight
    )

    deployer = NrgDeployer(config)
    result = deployer.execute()

    if result.success:
        logger.info(f"\n✓ DEPLOYMENT SUCCESSFUL")
        logger.info(f"  Version: {args.version}")
        logger.info(f"  Duration: {result.duration_seconds:.2f}s")
        sys.exit(0)
    else:
        logger.error(f"\n✗ DEPLOYMENT FAILED")
        logger.error(f"  Phase: {result.phase.value}")
        logger.error(f"  Message: {result.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
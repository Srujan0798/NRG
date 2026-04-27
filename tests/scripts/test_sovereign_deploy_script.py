import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "infrastructure"
    / "helm"
    / "nrg"
    / "scripts"
    / "sovereign_deploy.py"
)


def test_sovereign_deploy_script_help_runs():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "NRG Sovereign Landing" in result.stdout


def test_sovereign_deploy_script_imports():
    spec = importlib.util.spec_from_file_location("sovereign_deploy", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)

    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert hasattr(module, "NrgDeployer")
    assert hasattr(module, "DeploymentConfig")

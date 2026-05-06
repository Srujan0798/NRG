from __future__ import annotations

from pathlib import Path

from scripts import run_final_external_gates as gates


def _result(command: list[str], output: Path | None, stdout: str, exit_code: int = 0) -> dict:
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(stdout)
    return {
        "command": " ".join(command),
        "exit_code": exit_code,
        "duration_ms": 0,
        "output": str(output) if output else None,
    }


def test_cluster_load_blocks_without_kubeconfig(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setattr(gates.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, *, output=None, **_kwargs):
        calls.append(command)
        if command == ["kubectl", "config", "current-context"]:
            return _result(command, output, "colima\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(gates, "_run", fake_run)

    result = gates.load_gate(tmp_path, run_cluster_load=True)

    assert result["status"] == "BLOCKED"
    assert "KUBECONFIG" in result["missing"]
    assert ["kubectl", "cluster-info"] not in calls
    assert not any(call[:2] == ["bash", "tests/load/run-locust-k8s.sh"] for call in calls)


def test_cluster_load_blocks_local_kube_context(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    monkeypatch.setenv("KUBECONFIG", str(tmp_path / "kubeconfig"))
    monkeypatch.setattr(gates.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, *, output=None, **_kwargs):
        calls.append(command)
        if command == ["kubectl", "config", "current-context"]:
            return _result(command, output, "colima\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(gates, "_run", fake_run)

    result = gates.load_gate(tmp_path, run_cluster_load=True)

    assert result["status"] == "BLOCKED"
    assert "non-local Kubernetes context required; current context is colima" in result["missing"]
    assert ["kubectl", "cluster-info"] not in calls


def test_cluster_load_blocks_context_outside_allowlist(monkeypatch, tmp_path):
    monkeypatch.setenv("KUBECONFIG", str(tmp_path / "kubeconfig"))
    monkeypatch.setenv("NRG_ALLOWED_CLUSTER_CONTEXTS", "sovereign-staging")
    monkeypatch.setattr(gates.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, *, output=None, **_kwargs):
        if command == ["kubectl", "config", "current-context"]:
            return _result(command, output, "other-cluster\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(gates, "_run", fake_run)

    result = gates.load_gate(tmp_path, run_cluster_load=True)

    assert result["status"] == "BLOCKED"
    assert "current Kubernetes context is not in NRG_ALLOWED_CLUSTER_CONTEXTS" in result["missing"]
    assert result["checks"]["allowed_contexts"] == ["sovereign-staging"]


def test_cluster_load_runs_for_explicit_allowed_non_local_context(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    monkeypatch.setenv("KUBECONFIG", str(tmp_path / "kubeconfig"))
    monkeypatch.setenv("NRG_ALLOWED_CLUSTER_CONTEXTS", "sovereign-staging")
    monkeypatch.setattr(gates.shutil, "which", lambda command: f"/usr/bin/{command}")

    def fake_run(command, *, output=None, **_kwargs):
        calls.append(command)
        if command == ["kubectl", "config", "current-context"]:
            return _result(command, output, "sovereign-staging\n")
        if command == ["kubectl", "cluster-info"]:
            return _result(command, output, "Kubernetes control plane is running\n")
        if command == ["bash", "tests/load/run-locust-k8s.sh", "production"]:
            return _result(command, output, "C4 PASS\n")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(gates, "_run", fake_run)

    result = gates.load_gate(tmp_path, run_cluster_load=True)

    assert result["status"] == "PASS"
    assert ["kubectl", "cluster-info"] in calls
    assert ["bash", "tests/load/run-locust-k8s.sh", "production"] in calls

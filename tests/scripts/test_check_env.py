import importlib.util
import subprocess
from types import SimpleNamespace
from pathlib import Path


def _load_check_env_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check-env.py"
    spec = importlib.util.spec_from_file_location("check_env_script", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_cloud_synthesis_false_is_valid_opt_in_default(tmp_path):
    module = _load_check_env_module()
    env_file = tmp_path / ".env"
    env_file.write_text("CLOUD_SYNTHESIS_ALLOWED=false\n")

    assert module.check_env_file(env_file) is True


def test_cloud_synthesis_true_is_valid_explicit_opt_in(tmp_path):
    module = _load_check_env_module()
    env_file = tmp_path / ".env"
    env_file.write_text("CLOUD_SYNTHESIS_ALLOWED=true\n")

    assert module.check_env_file(env_file) is True


def test_cloud_synthesis_rejects_non_boolean_values(tmp_path):
    module = _load_check_env_module()
    env_file = tmp_path / ".env"
    env_file.write_text("CLOUD_SYNTHESIS_ALLOWED=maybe\n")

    assert module.check_env_file(env_file) is False


def test_empty_staged_env_list_does_not_warn(monkeypatch, capsys):
    module = _load_check_env_module()

    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert module.check_staged_files() is True
    assert "Warning:" not in capsys.readouterr().out

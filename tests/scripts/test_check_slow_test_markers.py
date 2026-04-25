from pathlib import Path

from scripts.check_slow_test_markers import check_path


def _write_test(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def test_long_timeout_requires_slow_marker(tmp_path):
    test_file = _write_test(
        tmp_path / "test_sample.py",
        """
import pytest

@pytest.mark.timeout(31)
def test_expensive_path():
    assert True
""",
    )

    violations = check_path(test_file)

    assert len(violations) == 1
    assert violations[0].node_name == "test_expensive_path"


def test_slow_marker_allows_long_timeout(tmp_path):
    test_file = _write_test(
        tmp_path / "test_sample.py",
        """
import pytest

@pytest.mark.slow
@pytest.mark.timeout(120)
def test_expensive_path():
    assert True
""",
    )

    assert check_path(test_file) == []


def test_module_slow_marker_allows_long_timeout(tmp_path):
    test_file = _write_test(
        tmp_path / "test_sample.py",
        """
import pytest

pytestmark = pytest.mark.slow

@pytest.mark.timeout(120)
def test_expensive_path():
    assert True
""",
    )

    assert check_path(test_file) == []

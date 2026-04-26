from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCUSTFILE = ROOT / "tests/load/locustfile.py"


def test_locustfile_authenticates_from_environment_before_tasks():
    source = LOCUSTFILE.read_text()

    assert "LOAD_TEST_RESEARCHER_USER" in source
    assert "LOAD_TEST_RESEARCHER_PASS" in source
    assert "LOAD_TEST_GOV_USER" in source
    assert "LOAD_TEST_GOV_PASS" in source
    assert "LOAD_TEST_INDUSTRY_USER" in source
    assert "LOAD_TEST_INDUSTRY_PASS" in source
    assert "self.environment.runner.quit()" in source


def test_locustfile_posts_real_query_requests_with_bearer_header():
    source = LOCUSTFILE.read_text()

    assert '"/query"' in source
    assert "Authorization" in source
    assert "Bearer" in source

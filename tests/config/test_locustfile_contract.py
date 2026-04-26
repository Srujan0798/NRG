from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOCUSTFILE = ROOT / "tests/load/locustfile.py"
C4_LOCUSTFILE = ROOT / "tests/load/locustfile_c4.py"


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


def test_c4_locustfile_uses_current_credentials_and_response_keys():
    source = C4_LOCUSTFILE.read_text()

    assert "LOAD_TEST_GOV_USER" in source
    assert "LOAD_TEST_GOV_PASS" in source
    assert '"government-pass"' in source
    assert "gov-pass" not in source
    assert "sql_query" in source
    assert "sql_results" in source
    assert "_handle_query_response(resp)" in source

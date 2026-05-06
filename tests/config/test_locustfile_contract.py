from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
LOCUSTFILE = ROOT / "tests/load/locustfile.py"
C4_LOCUSTFILE = ROOT / "tests/load/locustfile_c4.py"
C4_PERFORMANCE_LOCUSTFILE = ROOT / "tests/performance/locustfile_c4.py"


def test_locustfile_authenticates_from_environment_before_tasks():
    source = LOCUSTFILE.read_text()

    assert "LOAD_TEST_RESEARCHER_USER" in source
    assert "LOAD_TEST_RESEARCHER_PASS" in source
    assert "LOAD_TEST_RESEARCHER_TOKEN" in source
    assert "LOAD_TEST_GOV_USER" in source
    assert "LOAD_TEST_GOV_PASS" in source
    assert "LOAD_TEST_GOV_TOKEN" in source
    assert "LOAD_TEST_INDUSTRY_USER" in source
    assert "LOAD_TEST_INDUSTRY_PASS" in source
    assert "LOAD_TEST_INDUSTRY_TOKEN" in source
    assert "self.environment.runner.quit()" in source


def test_locustfile_posts_real_query_requests_with_bearer_header():
    source = LOCUSTFILE.read_text()

    assert '"/query"' in source
    assert '"question": query_text' in source
    assert "time.perf_counter()" in source
    assert ".duration" not in source
    assert "Authorization" in source
    assert "Bearer" in source


def test_c4_locustfile_uses_current_credentials_and_response_keys():
    source = C4_LOCUSTFILE.read_text()

    assert "FastHttpUser" in source
    assert "from locust import HttpUser" not in source
    assert "(HttpUser)" not in source
    assert "LOAD_TEST_GOV_USER" in source
    assert "LOAD_TEST_GOV_PASS" in source
    assert '"government-pass"' in source
    assert "gov-pass" not in source
    assert "sql_query" in source
    assert "sql_results" in source
    assert "StopUser" in source
    assert "with user.client.post(" in source
    assert "user.client.headers.update" not in source
    assert 'name="/auth/login"' in source
    assert "_handle_query_response(resp)" in source


def test_c4_locustfile_declares_60_30_10_traffic_mix():
    source = C4_LOCUSTFILE.read_text()

    assert "C4FastPathUser" in source
    assert "C4FullPathUser" in source
    assert "C4AdversarialUser" in source
    assert "weight = 60" in source
    assert "weight = 30" in source
    assert "weight = 10" in source
    assert "DROP TABLE" in source


def test_c4_locustfile_defaults_match_documented_throughput_profile():
    source = C4_LOCUSTFILE.read_text()

    assert "throughput >= 100 RPS" in source
    assert '_wait_window("C4_FAST", 4, 10)' in source
    assert '_wait_window("C4_FULL", 6, 14)' in source
    assert '_wait_window("C4_ADVERSARIAL", 6, 14)' in source


def test_c4_locustfile_treats_429_as_failure():
    source = C4_LOCUSTFILE.read_text()

    assert "resp.status_code == 429" in source
    assert 'resp.failure("HTTP 429 rate limited")' in source
    assert 'resp.success()' not in source.split("resp.status_code == 429", 1)[1].split("else:", 1)[0]


def test_c4_locustfile_names_query_metrics_by_workload():
    source = C4_LOCUSTFILE.read_text()

    assert 'name="/query::researcher"' in source
    assert 'name="/query::government"' in source
    assert 'name="/query::adversarial"' in source
    assert 'name="/query"' not in source


def test_c4_performance_path_matches_phase7_runbook():
    source = C4_PERFORMANCE_LOCUSTFILE.read_text()

    assert "tests.load.locustfile_c4" in source
    assert "C4FastPathUser" in source
    assert "C4FullPathUser" in source
    assert "C4AdversarialUser" in source
    assert "C4ResearcherUser" in source
    assert "C4GovernmentUser" in source
    assert "C4IndustryUser" in source

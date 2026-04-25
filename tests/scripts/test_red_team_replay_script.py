from pathlib import Path


SCRIPT = Path("scripts/red_team_replay.sh")


def test_red_team_replay_uses_bounded_curl_timeouts():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "CURL_MAX_TIME" in source
    assert "curl -s --max-time \"$CURL_MAX_TIME\"" in source


def test_red_team_replay_fails_fast_and_does_not_lock_demo_users():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "get_token || exit 1" in source
    assert "rt_bruteforce_user" in source
    assert "wrongpassword$i" in source


def test_red_team_replay_never_counts_http_000_as_pass_or_warning():
    source = SCRIPT.read_text(encoding="utf-8")

    assert '[[ "$1" == *"HTTP 000"* ]]' in source
    assert 'Request timed out or connection failed' in source


def test_red_team_replay_xss_tests_fail_on_transport_errors():
    source = SCRIPT.read_text(encoding="utf-8")

    assert "XSS request timed out or connection failed" in source
    assert "CSP XSS request timed out or connection failed" in source

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

from pathlib import Path


def test_government_persona_uses_backend_seed_password():
    login_source = Path("frontend/src/components/Login.tsx").read_text()

    assert "username: 'gov_user'" in login_source
    assert "password: 'government-pass'" in login_source
    assert "password: 'gov-pass'" not in login_source

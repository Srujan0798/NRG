import pytest
from pathlib import Path

from src.auth import jwt_handler as jwt_handler_module
from src.auth.jwt_handler import JWTHandler, AuthError, validate_jwt_secret
from scripts.rotate_jwt_secret import generate_jwt_secret


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
        users={},
    )


def test_generates_and_verifies_access_and_refresh_tokens(jwt_handler):
    user = {
        "user_id": "user-1",
        "username": "researcher_user",
        "role": "researcher",
        "tier": 1,
        "researcher_id": "researcher-1",
    }

    tokens = jwt_handler.issue_token_pair(user)

    access_claims = jwt_handler.verify_access_token(tokens["access_token"])
    refresh_claims = jwt_handler.verify_refresh_token(tokens["refresh_token"])

    assert access_claims["sub"] == "user-1"
    assert access_claims["role"] == "researcher"
    assert access_claims["tier"] == 1
    assert access_claims["token_type"] == "access"
    assert access_claims["iss"] == "researcher"
    assert refresh_claims["token_type"] == "refresh"


def test_jwt_secret_length_returns_unhealthy_status(monkeypatch):
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("JWT_SECRET", "short-secret")

    handler = JWTHandler(users={})
    health = handler.jwt_secret_health()
    assert health["status"] == "unhealthy"
    assert health["valid"] is False
    assert health["enforced"] is False


def test_short_explicit_test_fixture_secret_is_allowed():
    handler = JWTHandler(algorithm="HS256", secret_key="test-secret", users={})

    assert handler.jwt_secret_health()["status"] == "test_override"


def test_rotation_script_generates_32_byte_secret():
    secret = generate_jwt_secret(num_bytes=32)

    assert validate_jwt_secret(secret) is True
    assert len(secret.encode("utf-8")) >= 32


def test_refresh_rotates_refresh_token_and_revokes_old_one(jwt_handler):
    user = {
        "user_id": "user-2",
        "username": "gov_user",
        "role": "government",
        "tier": 2,
    }
    tokens = jwt_handler.issue_token_pair(user)

    refreshed = jwt_handler.refresh_access_token(tokens["refresh_token"])

    assert refreshed["access_token"] != tokens["access_token"]
    assert refreshed["refresh_token"] != tokens["refresh_token"]

    with pytest.raises(AuthError):
        jwt_handler.verify_refresh_token(tokens["refresh_token"])


def test_revoked_access_token_is_rejected(jwt_handler):
    user = {
        "user_id": "user-3",
        "username": "industry_user",
        "role": "industry",
        "tier": 3,
    }
    tokens = jwt_handler.issue_token_pair(user)

    jwt_handler.revoke_token(tokens["access_token"])

    with pytest.raises(AuthError):
        jwt_handler.verify_access_token(tokens["access_token"])


def test_production_password_environment_names_are_supported(monkeypatch):
    monkeypatch.delenv("RESEARCHER_PASSWORD", raising=False)
    monkeypatch.delenv("GOV_PASSWORD", raising=False)
    monkeypatch.delenv("INDUSTRY_PASSWORD", raising=False)
    monkeypatch.setenv("RESEARCHER_PASSWORD", "release-researcher-pass")
    monkeypatch.setenv("GOV_PASSWORD", "release-government-pass")
    monkeypatch.setenv("INDUSTRY_PASSWORD", "release-industry-pass")

    users = jwt_handler_module.build_default_users()
    handler = JWTHandler(
        algorithm="HS256",
        secret_key="test-secret",
        users=users,
    )

    researcher = handler.authenticate_user("researcher_user", "release-researcher-pass")
    government = handler.authenticate_user("gov_user", "release-government-pass")
    industry = handler.authenticate_user("industry_user", "release-industry-pass")
    assert researcher["role"] == "researcher"
    assert government["role"] == "government"
    assert industry["role"] == "industry"


def test_auth_code_does_not_support_forbidden_password_aliases():
    source = Path("src/auth/jwt_handler.py").read_text()

    assert "DEMO_" not in source


def test_refresh_token_survives_handler_restart_with_store(tmp_path, monkeypatch):
    db_path = tmp_path / "tokens.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    user = {
        "user_id": "user-persisted",
        "username": "researcher_user",
        "role": "researcher",
        "tier": 1,
    }
    first_handler = JWTHandler(algorithm="HS256", secret_key="test-secret", users={})
    tokens = first_handler.issue_token_pair(user)

    restarted_handler = JWTHandler(algorithm="HS256", secret_key="test-secret", users={})
    claims = restarted_handler.verify_refresh_token(tokens["refresh_token"])

    assert claims["sub"] == "user-persisted"


def test_logout_revokes_refresh_token_in_store(tmp_path, monkeypatch):
    db_path = tmp_path / "tokens.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    user = {
        "user_id": "user-revoked",
        "username": "researcher_user",
        "role": "researcher",
        "tier": 1,
    }
    handler = JWTHandler(algorithm="HS256", secret_key="test-secret", users={})
    tokens = handler.issue_token_pair(user)
    handler.revoke_token(tokens["refresh_token"])

    restarted_handler = JWTHandler(algorithm="HS256", secret_key="test-secret", users={})
    with pytest.raises(AuthError):
        restarted_handler.verify_refresh_token(tokens["refresh_token"])

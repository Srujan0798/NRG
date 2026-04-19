import pytest

from src.auth import jwt_handler as jwt_handler_module
from src.auth.jwt_handler import JWTHandler, AuthError


@pytest.fixture
def jwt_handler():
    return JWTHandler(
        secret_key="test-secret",
        access_token_ttl_seconds=300,
        refresh_token_ttl_seconds=3600,
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


def test_demo_password_environment_names_are_supported(monkeypatch):
    monkeypatch.delenv("RESEARCHER_PASSWORD", raising=False)
    monkeypatch.setenv("DEMO_RESEARCHER_PASSWORD", "demo-researcher-pass")

    users = jwt_handler_module.build_default_users()
    handler = JWTHandler(
        algorithm="HS256",
        secret_key="test-secret",
        users=users,
    )

    user = handler.authenticate_user("researcher_user", "demo-researcher-pass")
    assert user["role"] == "researcher"

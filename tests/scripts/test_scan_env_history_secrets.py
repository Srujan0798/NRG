from scripts.scan_env_history_secrets import Finding, is_secret_assignment, print_text


def test_secret_assignment_detects_sensitive_keys_without_value_leak():
    result = is_secret_assignment("DATABASE_URL=postgres://user:pass@localhost:5432/nrg")

    assert result is not None
    key, value = result
    assert key == "DATABASE_URL"
    assert value == "postgres://user:pass@localhost:5432/nrg"


def test_secret_assignment_ignores_placeholders_and_non_secret_keys():
    assert is_secret_assignment("JWT_SECRET=changeme") is None
    assert is_secret_assignment("JWT_ALGORITHM=HS256") is None
    assert is_secret_assignment("JWT_PUBLIC_KEY_PATH=/run/keys/jwt.pub") is None
    assert is_secret_assignment("SERVICE_URL=https://localhost:8000") is None
    assert is_secret_assignment("# PASSWORD=real-value") is None


def test_text_output_redacts_secret_value(capsys):
    finding = Finding(
        commit="abc123def4567890",
        path=".env.prod",
        line=7,
        key="JWT_SECRET",
        value_length=18,
        value_sha256="0123456789ab",
    )

    print_text([finding], commits_scanned=1, file_versions=1, max_findings=10)

    output = capsys.readouterr().out
    assert "S3-09 env history scan: FAIL" in output
    assert "JWT_SECRET len=18 sha256=0123456789ab" in output
    assert "real-value" not in output

from scripts.scan_env_history_secrets import (
    Finding,
    build_remediation_summary,
    is_secret_assignment,
    print_text,
    rotation_classes_for_key,
)


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


def test_remediation_summary_groups_paths_keys_and_rotation_classes():
    findings = [
        Finding(
            commit="abc123",
            path=".env.prod",
            line=1,
            key="POSTGRES_PASSWORD",
            value_length=24,
            value_sha256="aaa111bbb222",
        ),
        Finding(
            commit="def456",
            path=".env.prod",
            line=2,
            key="POSTGRES_PASSWORD",
            value_length=24,
            value_sha256="aaa111bbb222",
        ),
        Finding(
            commit="def456",
            path=".env.staging",
            line=3,
            key="JWT_SECRET",
            value_length=32,
            value_sha256="ccc333ddd444",
        ),
        Finding(
            commit="fed321",
            path=".env.staging",
            line=4,
            key="OPENAI_API_KEY",
            value_length=48,
            value_sha256="eee555fff666",
        ),
    ]

    summary = build_remediation_summary(findings, commits_scanned=3, file_versions=4)

    assert summary["status"] == "FAIL"
    assert summary["finding_count"] == 4
    assert summary["unique_secret_fingerprint_count"] == 3
    assert summary["affected_paths"] == [".env.prod", ".env.staging"]
    assert summary["affected_keys"] == ["JWT_SECRET", "OPENAI_API_KEY", "POSTGRES_PASSWORD"]
    assert summary["rotation_classes"] == ["jwt", "model_api", "postgresql"]
    assert summary["filter_repo_args"] == [
        "--path",
        ".env.prod",
        "--path",
        ".env.staging",
    ]
    assert "rotate all affected credential classes before unfreezing writes" in summary["required_actions"]


def test_remediation_summary_pass_when_no_findings():
    summary = build_remediation_summary([], commits_scanned=1, file_versions=0)

    assert summary["status"] == "PASS"
    assert summary["required_actions"] == []
    assert summary["affected_paths"] == []


def test_rotation_class_mapping_keeps_unknowns_visible():
    assert rotation_classes_for_key("REDIS_URL") == ["redis"]
    assert rotation_classes_for_key("RESEARCHER_PASSWORD") == ["acceptance_users"]
    assert rotation_classes_for_key("SOME_PRIVATE_KEY") == ["unknown_secret"]

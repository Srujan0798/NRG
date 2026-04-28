from pathlib import Path

from scripts.check_jwt_secret_config import scan_config_paths


def test_committed_jwt_secret_placeholders_meet_minimum_length():
    repo_root = Path(__file__).resolve().parents[2]
    findings = scan_config_paths(
        [
            repo_root / ".env.example",
            *sorted((repo_root / "infrastructure/helm/nrg").glob("values*.yaml")),
        ]
    )

    assert not findings, "\n".join(str(finding) for finding in findings)

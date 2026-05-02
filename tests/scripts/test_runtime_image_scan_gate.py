import json

from scripts.runtime_image_scan_gate import (
    build_report,
    summarize_pip_audit,
    summarize_trivy,
)


def _write_json(path, data):
    path.write_text(json.dumps(data))


def _trivy(vulnerabilities):
    return {"Results": [{"Target": "image", "Vulnerabilities": vulnerabilities}]}


def _pip_audit(vulns_by_package):
    return {
        "dependencies": [
            {"name": name, "version": "1.0.0", "vulns": vulns}
            for name, vulns in vulns_by_package.items()
        ]
    }


def test_runtime_image_gate_accepts_clean_frontend_nginx_and_no_fix_api_boundary(tmp_path):
    frontend = tmp_path / "frontend.json"
    nginx = tmp_path / "nginx.json"
    api_pip = tmp_path / "api_pip.json"
    api_strict = tmp_path / "api_strict.json"
    api_fixable = tmp_path / "api_fixable.json"

    _write_json(frontend, _trivy([]))
    _write_json(nginx, _trivy([]))
    _write_json(api_pip, _pip_audit({"fastapi": []}))
    _write_json(
        api_strict,
        _trivy(
            [
                {
                    "VulnerabilityID": "CVE-NOFIX",
                    "PkgName": "libsystemd0",
                    "Severity": "HIGH",
                }
            ]
        ),
    )
    _write_json(api_fixable, _trivy([]))

    report, ok = build_report(
        summarize_trivy(frontend),
        summarize_trivy(nginx),
        summarize_pip_audit(api_pip),
        summarize_trivy(api_strict),
        summarize_trivy(api_fixable),
    )

    assert ok is True
    assert "API runtime strict Trivy boundary | PARTIAL" in report
    assert "high=1" in report


def test_runtime_image_gate_fails_fixable_api_high(tmp_path):
    clean = tmp_path / "clean.json"
    api_pip = tmp_path / "api_pip.json"
    api_strict = tmp_path / "api_strict.json"
    api_fixable = tmp_path / "api_fixable.json"

    _write_json(clean, _trivy([]))
    _write_json(api_pip, _pip_audit({"fastapi": []}))
    _write_json(api_strict, _trivy([]))
    _write_json(
        api_fixable,
        _trivy(
            [
                {
                    "VulnerabilityID": "CVE-FIXABLE",
                    "PkgName": "openssl",
                    "Severity": "HIGH",
                    "FixedVersion": "1.0.1",
                }
            ]
        ),
    )

    report, ok = build_report(
        summarize_trivy(clean),
        summarize_trivy(clean),
        summarize_pip_audit(api_pip),
        summarize_trivy(api_strict),
        summarize_trivy(api_fixable),
    )

    assert ok is False
    assert "API fixable HIGH/CRITICAL Trivy scan has findings" in report


def test_runtime_image_gate_fails_pip_audit_vulnerability(tmp_path):
    clean = tmp_path / "clean.json"
    api_pip = tmp_path / "api_pip.json"

    _write_json(clean, _trivy([]))
    _write_json(api_pip, _pip_audit({"requests": [{"id": "CVE-1"}]}))

    report, ok = build_report(
        summarize_trivy(clean),
        summarize_trivy(clean),
        summarize_pip_audit(api_pip),
        summarize_trivy(clean),
        summarize_trivy(clean),
    )

    assert ok is False
    assert "API pip-audit has vulnerable packages" in report

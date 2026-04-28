from pathlib import Path


def test_login_presets_use_acceptance_personas():
    login_source = Path("frontend/src/components/Login.tsx").read_text()
    auth_source = Path("frontend/src/services/authService.ts").read_text()

    for source in (login_source, auth_source):
        assert "researcher@iitgn.ac.in" in source
        assert "Researcher@2026" in source
        assert "ministry@nrg.gov.in" in source
        assert "Ministry@2026" in source
        assert "partner@industry.in" in source
        assert "Industry@2026" in source

    assert "usernamePlaceholder: 'researcher@iitgn.ac.in'" in login_source
    assert "emailLabel: 'Email'" in login_source

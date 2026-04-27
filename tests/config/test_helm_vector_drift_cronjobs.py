from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
VALUES = ROOT / "infrastructure/helm/nrg/values.yaml"
CRONJOB = ROOT / "infrastructure/helm/nrg/templates/monitors/vector-drift-cronjobs.yaml"


def test_vector_drift_cronjob_template_declares_lightweight_and_deep_checks():
    source = CRONJOB.read_text()

    assert "nrg-vector-drift-lightweight" in source
    assert "nrg-vector-drift-deep" in source
    assert "--check-only" in source
    assert "scripts/vector_drift_check.py --json" in source
    assert "*/5 * * * *" in source
    assert "30 2 * * *" in source


def test_vector_drift_schedules_are_configurable_in_values():
    values = yaml.safe_load(VALUES.read_text())

    assert values["vectorDrift"]["enabled"] is True
    assert values["vectorDrift"]["lightweightSchedule"] == "*/5 * * * *"
    assert values["vectorDrift"]["deepSchedule"] == "30 2 * * *"

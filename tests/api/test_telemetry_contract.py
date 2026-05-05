from __future__ import annotations

import re
from pathlib import Path

from src.api.routes.telemetry import TELEMETRY_EVENT_NAMES, TelemetryEventIn


REPO_ROOT = Path(__file__).resolve().parents[2]


def _frontend_telemetry_events() -> set[str]:
    source = (REPO_ROOT / "frontend/src/lib/telemetry.ts").read_text()
    match = re.search(r"telemetryEventNames\s*=\s*\[(?P<body>.*?)\]\s+as const", source, re.S)
    assert match, "frontend telemetryEventNames array not found"
    return set(re.findall(r"'([^']+)'", match.group("body")))


def test_backend_accepts_every_frontend_telemetry_event_name() -> None:
    frontend_events = _frontend_telemetry_events()

    assert frontend_events - TELEMETRY_EVENT_NAMES == set()

    for event_name in sorted(frontend_events):
        TelemetryEventIn(
            schema_version=1,
            event_id=f"tel_{event_name.replace('.', '_')}",
            event=event_name,
            ts="2026-05-05T11:00:00Z",
            session_id="researcher-acceptance-iitgn",
            route="/app",
            payload={"source": "contract-test"},
        )

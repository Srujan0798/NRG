"""PagerDuty alerting integration for NRG SLO breaches."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class PagerDutyClient:
    """Lightweight PagerDuty Events API v2 client."""

    def __init__(self, integration_key: str | None = None):
        self.integration_key = integration_key or os.getenv("PAGERDUTY_INTEGRATION_KEY", "")
        self.routing_key = os.getenv("PAGERDUTY_ROUTING_KEY", self.integration_key)
        self._enabled = bool(self.routing_key)

    def is_enabled(self) -> bool:
        return self._enabled

    def trigger(
        self,
        summary: str,
        severity: str = "warning",
        source: str = "nrg-api",
        custom_details: dict[str, Any] | None = None,
    ) -> bool:
        """Send a PagerDuty incident trigger event.

        severity: critical | error | warning | info
        """
        if not self._enabled:
            logger.debug("PagerDuty disabled (no routing key)")
            return False

        import httpx

        payload = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "dedup_key": f"nrg-{source}-{severity}",
            "payload": {
                "summary": summary,
                "source": source,
                "severity": severity,
                "custom_details": custom_details or {},
            },
        }

        try:
            response = httpx.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10.0,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code in (202, 200):
                logger.info("PagerDuty alert sent: %s [%s]", summary, severity)
                return True
            else:
                logger.warning("PagerDuty API returned %d: %s", response.status_code, response.text)
                return False
        except Exception as exc:
            logger.warning("Failed to send PagerDuty alert: %s", exc)
            return False


_pagerduty: PagerDutyClient | None = None


def get_pagerduty() -> PagerDutyClient:
    global _pagerduty
    if _pagerduty is None:
        _pagerduty = PagerDutyClient()
    return _pagerduty


def send_critical_alert(summary: str, **kwargs) -> bool:
    client = get_pagerduty()
    return client.trigger(summary=summary, severity="critical", **kwargs)


def send_warning_alert(summary: str, **kwargs) -> bool:
    client = get_pagerduty()
    return client.trigger(summary=summary, severity="warning", **kwargs)

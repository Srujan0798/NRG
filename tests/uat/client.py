"""Shared authenticated client for persona UAT flows."""

from tests.security.redteam.client import LiveAPIClient


ROLE_BY_TIER = {
    "tier1": "researcher",
    "tier2": "government",
    "tier3": "industry",
}


class UATClient(LiveAPIClient):
    def query_for_tier(self, query: str, tier: str):
        return self.query(query, role=ROLE_BY_TIER[tier])

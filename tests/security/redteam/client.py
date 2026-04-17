"""Shared authenticated client for live security testing."""

from __future__ import annotations

import os

import requests


ROLE_CREDENTIALS = {
    "researcher": ("researcher_user", "researcher-pass"),
    "government": ("gov_user", "government-pass"),
    "industry": ("industry_user", "industry-pass"),
}


class LiveAPIClient:
    def __init__(self, base_url: str | None = None, timeout: int = 10):
        self.base_url = base_url or os.getenv("NRG_BASE_URL", "http://localhost:8000")
        self.timeout = timeout

    def login(self, role: str) -> str:
        username, password = ROLE_CREDENTIALS[role]
        response = requests.post(
            f"{self.base_url}/login",
            json={"username": username, "password": password},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()["access_token"]

    def query(self, query: str, role: str = "researcher") -> requests.Response:
        token = self.login(role)
        return requests.post(
            f"{self.base_url}/query",
            json={"query": query},
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )

    def researchers(self, role: str = "researcher") -> requests.Response:
        token = self.login(role)
        return requests.get(
            f"{self.base_url}/researchers",
            headers={"Authorization": f"Bearer {token}"},
            timeout=self.timeout,
        )

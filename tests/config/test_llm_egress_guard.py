import pytest

from src.config import llm_config
from src.config.llm_config import LLMSettings, OpenAIResponsesClient
from src.security.egress.guard import SovereigntyViolation


class RecordingSovereignClient:
    def __init__(self):
        self.payloads = []

    def inspect_payload(self, payload):
        self.payloads.append(payload)
        if "abstract" in str(payload).lower():
            raise SovereigntyViolation("raw abstract blocked", blocked_field="abstract")


def test_openai_client_inspects_payload_before_cloud_call(monkeypatch):
    guard = RecordingSovereignClient()
    monkeypatch.setattr(llm_config, "create_sovereign_client", lambda: guard)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("HTTP call must not happen after sovereignty violation")

    monkeypatch.setattr(llm_config.requests, "post", fail_if_called)

    client = OpenAIResponsesClient(
        LLMSettings(
            provider="openai",
            api_key="test-openai-key",
            model="gpt-5-mini",
        )
    )

    with pytest.raises(SovereigntyViolation):
        client.generate(
            system_prompt="You are a model.",
            user_prompt="Summarize publications.abstract raw content",
            conversation_history=[],
        )

    assert guard.payloads

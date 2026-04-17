import pytest

from src.config.llm_config import (
    LLMConfigError,
    LLMSettings,
    OpenAIResponsesClient,
    load_llm_settings,
)


def test_load_llm_settings_for_openai(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-mini")

    settings = load_llm_settings()

    assert settings.provider == "openai"
    assert settings.api_key == "test-openai-key"
    assert settings.model == "gpt-5-mini"


def test_openai_client_extracts_output_text(monkeypatch):
    captured_request = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"output_text": "Cloud answer"}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured_request["url"] = url
        captured_request["headers"] = headers
        captured_request["json"] = json
        captured_request["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("src.config.llm_config.requests.post", fake_post)

    client = OpenAIResponsesClient(
        LLMSettings(
            provider="openai",
            api_key="test-openai-key",
            model="gpt-5-mini",
            request_timeout_seconds=12,
        )
    )

    result = client.generate(
        system_prompt="You are a test model.",
        user_prompt="Summarize the result.",
        conversation_history=[{"query": "Earlier question", "response": "Earlier answer"}],
    )

    assert result == "Cloud answer"
    assert captured_request["url"] == "https://api.openai.com/v1/responses"
    assert captured_request["headers"]["Authorization"] == "Bearer test-openai-key"
    assert captured_request["json"]["model"] == "gpt-5-mini"
    assert captured_request["json"]["instructions"] == "You are a test model."


def test_load_llm_settings_requires_provider_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(LLMConfigError):
        load_llm_settings()

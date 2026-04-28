"""Tests for llm_config module with mocked providers."""

import pytest
import os
from unittest.mock import patch, MagicMock

from src.config.llm_config import (
    load_llm_settings,
    LLMConfigError,
    LLMSettings,
    MinimaxLLMClient,
    _env,
    _inspect_cloud_payload,
    get_llm_client,
)


class TestLoadLLMSettings:
    def test_missing_openai_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMConfigError, match="OPENAI_API_KEY"):
                load_llm_settings("openai")

    def test_missing_gemini_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMConfigError, match="GEMINI_API_KEY"):
                load_llm_settings("gemini")

    def test_missing_nvidia_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMConfigError, match="NVIDIA_API_KEY"):
                load_llm_settings("nvidia")

    def test_missing_anthropic_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(LLMConfigError, match="ANTHROPIC_API_KEY"):
                load_llm_settings("anthropic")

    def test_unsupported_provider_raises(self):
        with pytest.raises(LLMConfigError, match="Unsupported"):
            load_llm_settings("unsupported_provider")

    def test_openai_settings_loaded(self):
        env = {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-4o"}
        with patch.dict(os.environ, env, clear=True):
            settings = load_llm_settings("openai")
            assert settings.provider == "openai"
            assert settings.api_key == "test-key"
            assert settings.model == "gpt-4o"

    def test_gemini_settings_loaded(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "gem-key"}, clear=False):
            settings = load_llm_settings("gemini")
            assert settings.provider == "gemini"
            assert settings.api_key == "gem-key"

    def test_nvidia_settings_loaded(self):
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "nv-key"}, clear=False):
            settings = load_llm_settings("nvidia")
            assert settings.provider == "nvidia"

    def test_anthropic_settings_loaded(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "ant-key"}, clear=False):
            settings = load_llm_settings("anthropic")
            assert settings.provider == "anthropic"

    def test_azure_settings_loaded(self):
        env = {
            "AZURE_OPENAI_API_KEY": "az-key",
            "AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com",
            "AZURE_OPENAI_DEPLOYMENT": "gpt-4",
        }
        with patch.dict(os.environ, env, clear=False):
            settings = load_llm_settings("azure")
            assert settings.provider == "azure"
            assert settings.azure_deployment == "gpt-4"


class TestEnv:
    def test_returns_value(self):
        with patch.dict(os.environ, {"TEST_VAR": "hello"}):
            assert _env("TEST_VAR") == "hello"

    def test_returns_default_when_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _env("MISSING", "default") == "default"

    def test_returns_default_when_replace_me(self):
        with patch.dict(os.environ, {"VAR": "REPLACE_ME"}):
            assert _env("VAR", "fallback") == "fallback"


class TestInspectCloudPayload:
    @patch("src.config.llm_config.create_sovereign_client")
    def test_calls_inspect_payload(self, mock_create):
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        _inspect_cloud_payload({"model": "test"})
        mock_client.inspect_payload.assert_called_once_with({"model": "test"})


class TestGetLLMClient:
    def test_returns_none_on_config_error(self):
        get_llm_client.cache_clear()
        with patch.dict(os.environ, {}, clear=True):
            result = get_llm_client()
            assert result is None

    def test_cached(self):
        get_llm_client.cache_clear()
        with patch.dict(os.environ, {}, clear=True):
            assert get_llm_client() is None
            assert get_llm_client() is None
        get_llm_client.cache_clear()

class TestMinimaxDefaults:
    @patch("src.config.llm_config.requests.post")
    @patch("src.config.llm_config._inspect_cloud_payload")
    def test_synthesis_defaults_are_low_drift(self, mock_inspect, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "answer"}}]}
        mock_post.return_value = mock_response
        client = MinimaxLLMClient(
            LLMSettings(provider="minimax", api_key="test-key", model="minimax-m2.7")
        )

        client.generate("Synthesize a research answer", "question", [])

        payload = mock_post.call_args.kwargs["json"]
        assert payload["temperature"] == 0.2
        assert payload["top_p"] == 0.9

    @patch("src.config.llm_config.requests.post")
    @patch("src.config.llm_config._inspect_cloud_payload")
    def test_sql_generation_defaults_are_deterministic(self, mock_inspect, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "SELECT 1"}}]}
        mock_post.return_value = mock_response
        client = MinimaxLLMClient(
            LLMSettings(provider="minimax", api_key="test-key", model="minimax-m2.7")
        )

        client.generate("You are a text_to_sql generator. Return SQL only.", "count rows", [])

        payload = mock_post.call_args.kwargs["json"]
        assert payload["temperature"] == 0.0
        assert payload["top_p"] == 0.9

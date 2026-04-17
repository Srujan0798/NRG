"""Cloud LLM configuration and provider clients with sovereign mesh fallback."""

from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Protocol, Optional

import requests


logger = logging.getLogger(__name__)


class LLMConfigError(RuntimeError):
    """Raised when cloud LLM configuration is missing or invalid."""


class LLMProviderError(RuntimeError):
    """Raised when LLM provider request fails."""


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    api_key: str
    model: str
    base_url: str | None = None
    request_timeout_seconds: int = 30
    azure_api_version: str = "2024-10-21"
    azure_deployment: str | None = None


@dataclass
class LLMMeshConfig:
    """Configuration for sovereign LLM mesh with fallback."""
    primary_provider: str
    fallback_order: list[str]
    max_retries: int = 3
    retry_delay_seconds: int = 5
    request_timeout_seconds: int = 30


class LLMClient(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str: ...


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "" or "REPLACE_ME" in value:
        return default
    return value.strip()


def load_llm_settings(provider_name: str | None = None) -> LLMSettings:
    provider = (provider_name or _env("LLM_PROVIDER", "openai") or "openai").lower()
    timeout = int(_env("LLM_REQUEST_TIMEOUT_SECONDS", "30") or "30")

    if provider == "gemini":
        api_key = _env("GEMINI_API_KEY")
        if not api_key:
            raise LLMConfigError("GEMINI_API_KEY is required for provider 'gemini'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("GEMINI_MODEL", "gemini-1.5-flash") or "gemini-1.5-flash",
            base_url=None,
            request_timeout_seconds=timeout,
        )

    if provider == "openai":
        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            raise LLMConfigError("OPENAI_API_KEY is required for provider 'openai'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("OPENAI_MODEL", "gpt-4-turbo") or "gpt-4-turbo",
            base_url=_env("OPENAI_BASE_URL", "https://api.openai.com/v1/responses"),
            request_timeout_seconds=timeout,
        )

    if provider == "anthropic":
        api_key = _env("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMConfigError("ANTHROPIC_API_KEY is required for provider 'anthropic'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
            or "claude-3-5-sonnet-latest",
            base_url=_env("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1/messages"),
            request_timeout_seconds=timeout,
        )

    if provider == "azure":
        api_key = _env("AZURE_OPENAI_API_KEY")
        endpoint = _env("AZURE_OPENAI_ENDPOINT")
        deployment = _env("AZURE_OPENAI_DEPLOYMENT")
        if not api_key or not endpoint or not deployment:
            raise LLMConfigError(
                "AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT are required for provider 'azure'"
            )
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("AZURE_OPENAI_MODEL", deployment) or deployment,
            base_url=endpoint.rstrip("/"),
            request_timeout_seconds=timeout,
            azure_api_version=_env("AZURE_OPENAI_API_VERSION", "2024-10-21")
            or "2024-10-21",
            azure_deployment=deployment,
        )

    raise LLMConfigError(f"Unsupported LLM provider: {provider}")


class LLMMeshClient:
    """Client that implements multi-provider fallback mesh."""

    def __init__(self, fallback_order: list[str]):
        self.fallback_order = fallback_order
        self.clients: dict[str, LLMClient] = {}

    def _get_client(self, provider: str) -> LLMClient | None:
        if provider in self.clients:
            return self.clients[provider]
        
        try:
            settings = load_llm_settings(provider)
            if provider == "openai":
                client = OpenAIResponsesClient(settings)
            elif provider == "anthropic":
                client = AnthropicMessagesClient(settings)
            elif provider == "azure":
                client = AzureOpenAIClient(settings)
            elif provider == "gemini":
                client = GeminiGenAIClient(settings)
            else:
                return None
            
            self.clients[provider] = client
            return client
        except LLMConfigError:
            return None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        errors = []
        for provider in self.fallback_order:
            client = self._get_client(provider)
            if not client:
                continue
            
            try:
                logger.info(f"Attempting LLM generation with provider: {provider}")
                return client.generate(system_prompt, user_prompt, conversation_history)
            except Exception as e:
                logger.warning(f"Provider {provider} failed: {e}")
                errors.append(f"{provider}: {str(e)}")
        
        raise LLMProviderError(f"All LLM providers in mesh failed: {'; '.join(errors)}")


class OpenAIResponsesClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        response = requests.post(
            self.settings.base_url or "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.settings.model,
                "instructions": system_prompt,
                "input": _build_openai_input(conversation_history, user_prompt),
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("output_text"):
            return payload["output_text"]
        raise RuntimeError("OpenAI response did not include output_text")


class AnthropicMessagesClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        response = requests.post(
            self.settings.base_url or "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.settings.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.settings.model,
                "max_tokens": 800,
                "system": system_prompt,
                "messages": _build_message_history(conversation_history, user_prompt),
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("content", [])
        if content and isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            if text_parts:
                return "\n".join(text_parts).strip()
        raise RuntimeError("Anthropic response did not include text content")


class AzureOpenAIClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        if not self.settings.azure_deployment:
            raise LLMConfigError("Azure OpenAI deployment name is missing")

        url = (
            f"{self.settings.base_url}/openai/deployments/"
            f"{self.settings.azure_deployment}/chat/completions"
            f"?api-version={self.settings.azure_api_version}"
        )
        response = requests.post(
            url,
            headers={
                "api-key": self.settings.api_key,
                "Content-Type": "application/json",
            },
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *_build_message_history(conversation_history, user_prompt),
                ],
                "temperature": 0.2,
            },
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return content
        raise RuntimeError("Azure OpenAI response did not include a message content")


class GeminiGenAIClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.llm = ChatGoogleGenerativeAI(
                model=self.settings.model,
                google_api_key=self.settings.api_key
            )
        except ImportError:
            raise RuntimeError("langchain-google-genai not installed. Run pip install langchain-google-genai")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        
        history = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                history.append(HumanMessage(content=turn["query"]))
            if turn.get("response"):
                history.append(SystemMessage(content=turn["response"])) # Or appropriate role

        messages = [
            SystemMessage(content=system_prompt),
            *history,
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content


def _build_message_history(
    conversation_history: list[dict],
    user_prompt: str,
) -> list[dict]:
    messages: list[dict] = []

    for turn in conversation_history[-3:]:
        query = turn.get("query")
        response = turn.get("response")
        if query:
            messages.append({"role": "user", "content": query})
        if response:
            messages.append({"role": "assistant", "content": response})

    messages.append({"role": "user", "content": user_prompt})
    return messages


def _build_openai_input(
    conversation_history: list[dict],
    user_prompt: str,
) -> list[dict]:
    return [
        {
            "role": message["role"],
            "content": [{"type": "input_text", "text": message["content"]}],
        }
        for message in _build_message_history(conversation_history, user_prompt)
    ]


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient | None:
    fallback_order_str = _env("LLM_FALLBACK_ORDER")
    if fallback_order_str:
        fallback_order = [p.strip() for p in fallback_order_str.split(",") if p.strip()]
        if fallback_order:
            return LLMMeshClient(fallback_order)

    try:
        settings = load_llm_settings()
    except LLMConfigError:
        return None

    if settings.provider == "openai":
        return OpenAIResponsesClient(settings)
    if settings.provider == "anthropic":
        return AnthropicMessagesClient(settings)
    if settings.provider == "azure":
        return AzureOpenAIClient(settings)
    if settings.provider == "gemini":
        return GeminiGenAIClient(settings)

    return None


class SovereignLLMMesh:
    """
    Sovereign LLM Mesh with automatic fallback.
    
    Tries providers in order: primary → fallback1 → fallback2 → ...
    Ensures high availability for IITGN production.
    """
    
    def __init__(self):
        self.clients: dict[str, LLMClient] = {}
        self.mesh_config = self._load_mesh_config()
        self._initialize_clients()
    
    def _load_mesh_config(self) -> LLMMeshConfig:
        """Load mesh configuration from environment."""
        fallback_order_str = _env("LLM_FALLBACK_ORDER", "openai,anthropic,azure")
        fallback_order = [p.strip() for p in fallback_order_str.split(",")]
        
        return LLMMeshConfig(
            primary_provider=fallback_order[0] if fallback_order else "openai",
            fallback_order=fallback_order[1:] if len(fallback_order) > 1 else [],
            max_retries=int(_env("LLM_MAX_RETRIES", "3") or "3"),
            retry_delay_seconds=int(_env("LLM_RETRY_DELAY_SECONDS", "5") or "5"),
            request_timeout_seconds=int(_env("LLM_REQUEST_TIMEOUT_SECONDS", "30") or "30"),
        )
    
    def _initialize_clients(self):
        """Initialize all configured LLM clients."""
        all_providers = [self.mesh_config.primary_provider] + self.mesh_config.fallback_order
        
        for provider in all_providers:
            try:
                # Temporarily override provider setting
                original_provider = os.getenv("LLM_PROVIDER")
                os.environ["LLM_PROVIDER"] = provider
                
                settings = load_llm_settings()
                
                if provider == "openai":
                    self.clients[provider] = OpenAIResponsesClient(settings)
                elif provider == "anthropic":
                    self.clients[provider] = AnthropicMessagesClient(settings)
                elif provider == "azure":
                    self.clients[provider] = AzureOpenAIClient(settings)
                elif provider == "gemini":
                    self.clients[provider] = GeminiGenAIClient(settings)
                
                logger.info(f"✅ LLM Mesh: {provider} client initialized")
                
                # Restore original provider
                if original_provider:
                    os.environ["LLM_PROVIDER"] = original_provider
                    
            except Exception as e:
                logger.warning(f"⚠️ LLM Mesh: {provider} client failed: {e}")
        
        if not self.clients:
            raise LLMConfigError("No LLM providers available in mesh")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict] = None,
    ) -> str:
        """
        Generate response with automatic fallback.
        
        Tries primary provider, then falls back to others in order.
        """
        conversation_history = conversation_history or []
        provider_order = [self.mesh_config.primary_provider] + self.mesh_config.fallback_order
        available_providers = [p for p in provider_order if p in self.clients]
        
        if not available_providers:
            raise LLMProviderError("No LLM providers available in mesh")
        
        last_error = None
        
        for attempt in range(self.mesh_config.max_retries):
            for provider in available_providers:
                try:
                    client = self.clients[provider]
                    response = client.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        conversation_history=conversation_history,
                    )
                    
                    if len(response) > 0:
                        logger.info(f"✅ LLM Mesh: Response from {provider} (attempt {attempt + 1})")
                        return response
                    
                except Exception as e:
                    last_error = e
                    logger.warning(f"⚠️ LLM Mesh: {provider} failed (attempt {attempt + 1}): {e}")
                    
                    # Don't retry for configuration errors
                    if isinstance(e, LLMConfigError):
                        continue
                    
                    # Wait before retry
                    if attempt < self.mesh_config.max_retries - 1:
                        time.sleep(self.mesh_config.retry_delay_seconds)
        
        raise LLMProviderError(
            f"All LLM providers failed after {self.mesh_config.max_retries} attempts. "
            f"Last error: {last_error}"
        )
    
    def get_available_providers(self) -> list[str]:
        """Get list of available LLM providers in mesh."""
        return list(self.clients.keys())
    
    def health_check(self) -> dict:
        """Check health of all LLM providers in mesh."""
        health = {}
        
        for provider, client in self.clients.items():
            try:
                # Simple test query
                test_response = client.generate(
                    system_prompt="You are a test system.",
                    user_prompt="Respond with 'OK' only.",
                    conversation_history=[],
                )
                health[provider] = {
                    "status": "healthy",
                    "response_length": len(test_response)
                }
            except Exception as e:
                health[provider] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health


# Convenience function to get mesh client
def get_llm_mesh() -> SovereignLLMMesh:
    """Get sovereign LLM mesh with automatic fallback."""
    return SovereignLLMMesh()

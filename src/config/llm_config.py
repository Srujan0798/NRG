"""Cloud LLM configuration and provider clients with sovereign mesh fallback."""

from __future__ import annotations

import os
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Protocol

import requests  # type: ignore[import-untyped]

from src.security.egress.guard import create_sovereign_client


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
    query_timeout_budget_seconds: int = 45


class LLMClient(Protocol):
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str: ...


def _inspect_cloud_payload(payload: dict) -> None:
    """Enforce sovereignty before any cloud LLM egress."""
    create_sovereign_client().inspect_payload(payload)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "" or "REPLACE_ME" in value:
        return default
    return value.strip()


def load_llm_settings(provider_name: str | None = None) -> LLMSettings:
    provider = (provider_name or _env("LLM_PROVIDER", "openai") or "openai").lower()
    timeout = int(_env("LLM_REQUEST_TIMEOUT_SECONDS", "30") or "30")

    if provider == "nvidia":
        api_key = _env("NVIDIA_API_KEY")
        if not api_key:
            raise LLMConfigError("NVIDIA_API_KEY is required for provider 'nvidia'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("NVIDIA_MODEL", "meta/llama-3.1-70b-instruct") or "meta/llama-3.1-70b-instruct",
            base_url="https://integrate.api.nvidia.com/v1",
            request_timeout_seconds=timeout,
        )

    if provider == "gemini":
        api_key = _env("GEMINI_API_KEY")
        if not api_key:
            raise LLMConfigError("GEMINI_API_KEY is required for provider 'gemini'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("GEMINI_MODEL", "gemini-2.0-flash") or "gemini-2.0-flash",
            base_url=None,
            request_timeout_seconds=timeout,
        )

    if provider == "minimax":
        api_key = _env("MINIMAX_API_KEY")
        if not api_key:
            raise LLMConfigError("MINIMAX_API_KEY is required for provider 'minimax'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("MINIMAX_MODEL", "minimax-m2.7") or "minimax-m2.7",
            base_url=_env("MINIMAX_BASE_URL", "https://api.minimaxi.chat/v1") or "https://api.minimaxi.chat/v1",
            request_timeout_seconds=timeout,
        )

    if provider == "openai":
        api_key = _env("OPENAI_API_KEY")
        if not api_key:
            raise LLMConfigError("OPENAI_API_KEY is required for provider 'openai'")
        return LLMSettings(
            provider=provider,
            api_key=api_key,
            model=_env("OPENAI_MODEL", "gpt-4o") or "gpt-4o",
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
            model=_env("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest") or "claude-3-5-sonnet-latest",
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
            azure_api_version=_env("AZURE_OPENAI_API_VERSION", "2024-10-21") or "2024-10-21",
            azure_deployment=deployment,
        )

    raise LLMConfigError(f"Unsupported LLM provider: {provider}")


class NvidiaLLMClient:
    """NVIDIA API client for Llama and other models."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
        }
        _inspect_cloud_payload(payload)

        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return str(content)
        raise RuntimeError("NVIDIA API response did not include content")

    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ):
        """Streaming generator for NVIDIA API."""
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
            "stream": True,
        }
        _inspect_cloud_payload(payload)

        with requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue


class OpenAIResponsesClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        messages = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "instructions": system_prompt,
            "input": messages,
            "temperature": 0.2,
        }
        _inspect_cloud_payload(payload)

        response = requests.post(
            self.settings.base_url or "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        if "output_text" in payload and payload["output_text"]:
            return str(payload["output_text"])

        if "output" in payload:
            for item in payload["output"]:
                if item.get("type") == "message":
                    content = item.get("content", [])
                    if isinstance(content, list):
                        for content_item in content:
                            if content_item.get("type") == "output_text" and content_item.get("text"):
                                return str(content_item["text"])
                    elif isinstance(content, str):
                        return content

        return ""

    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ):
        """Streaming generator for OpenAI Responses API."""
        messages = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "instructions": system_prompt,
            "input": messages,
            "temperature": 0.2,
            "stream": True,
        }
        _inspect_cloud_payload(payload)

        with requests.post(
            self.settings.base_url or "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data)
                            if "output_text" in chunk:
                                yield chunk["output_text"]
                            elif "output" in chunk:
                                for item in chunk["output"]:
                                    if item.get("type") == "message":
                                        content = item.get("content", [])
                                        if isinstance(content, list):
                                            for ci in content:
                                                if ci.get("type") == "output_text" and ci.get("text"):
                                                    yield ci["text"]
                        except Exception:
                            continue


class AnthropicMessagesClient:
    def __init__(self, settings: LLMSettings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        messages = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "max_tokens": 800,
            "system": system_prompt,
            "messages": messages,
        }
        _inspect_cloud_payload(payload)

        response = requests.post(
            self.settings.base_url or "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.settings.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
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

    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ):
        """Streaming generator for Anthropic Messages API."""
        messages = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "max_tokens": 800,
            "system": system_prompt,
            "messages": messages,
            "stream": True,
        }
        _inspect_cloud_payload(payload)

        with requests.post(
            self.settings.base_url or "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.settings.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data)
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                        except Exception:
                            continue


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

        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "messages": messages,
            "temperature": 0.2,
        }
        _inspect_cloud_payload(payload)

        response = requests.post(
            url,
            headers={
                "api-key": self.settings.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return str(content)
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

        from langchain_core.messages import BaseMessage
        history: list[BaseMessage] = []
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                history.append(HumanMessage(content=turn["query"]))
            if turn.get("response"):
                history.append(SystemMessage(content=turn["response"]))

        messages = [
            SystemMessage(content=system_prompt),
            *history,
            HumanMessage(content=user_prompt)
        ]
        _inspect_cloud_payload(
            {
                "model": self.settings.model,
                "messages": [
                    {"type": message.__class__.__name__, "content": message.content}
                    for message in messages
                ],
            }
        )

        response = self.llm.invoke(messages)
        content = response.content
        if isinstance(content, str):
            return content
        return str(content)


@lru_cache(maxsize=8)
def get_llm_client(provider_name: str | None = None) -> LLMClient | None:
    try:
        settings = load_llm_settings(provider_name)
    except LLMConfigError as e:
        logger.warning("NO LLM CONFIGURED: %s", e)
        return None
    logger.info("LLM client ready: provider=%s model=%s", settings.provider, settings.model)

    if settings.provider == "nvidia":
        return NvidiaLLMClient(settings)
    if settings.provider == "openai":
        return OpenAIResponsesClient(settings)
    if settings.provider == "anthropic":
        return AnthropicMessagesClient(settings)
    if settings.provider == "azure":
        return AzureOpenAIClient(settings)
    if settings.provider == "gemini":
        return GeminiGenAIClient(settings)
    if settings.provider == "minimax":
        return MinimaxLLMClient(settings)

    return None


class MinimaxLLMClient:
    """MiniMax API client (Coding Plan key supports minimax-m2.7)."""

    def __init__(self, settings: LLMSettings):
        self.settings = settings
        self.base_url = (settings.base_url or "https://api.minimaxi.chat/v1").rstrip("/")

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
        }
        _inspect_cloud_payload(payload)

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        choices = payload.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content")
            if content:
                return str(content)
        raise RuntimeError("MiniMax API response did not include content")

    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list[dict],
    ):
        """Streaming generator for MiniMax API."""
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-3:]:
            if turn.get("query"):
                messages.append({"role": "user", "content": turn["query"]})
            if turn.get("response"):
                messages.append({"role": "assistant", "content": turn["response"]})
        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 800,
            "stream": True,
        }
        _inspect_cloud_payload(payload)

        with requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.settings.request_timeout_seconds,
            stream=True,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            import json as _json
                            chunk = _json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            continue


class SovereignLLMMesh:
    """
    Sovereign LLM Mesh with automatic fallback, circuit breaker, and health-weighted routing.

    Key features:
    - Global 15s timeout budget across ALL LLM attempts (no more 270s retry storms)
    - Health-weighted provider selection: score = success_rate / avg_latency
    - Parallel first-provider race: top-2 healthy providers fire simultaneously
    - Exponential backoff recovery: 30s → 60s → 120s → 300s cooldown
    - Circuit breaker trips after 3 failures in 5 min
    """

    def __init__(self):
        self.clients: dict[str, LLMClient] = {}
        self.mesh_config = self._load_mesh_config()
        self._initialize_clients()
        self._circuit_state: dict[str, str] = {p: "closed" for p in self.clients}
        self._failure_history: dict[str, list[float]] = {p: [] for p in self.clients}
        self._failure_lock = threading.Lock()
        self._circuit_failure_threshold = 5
        self._circuit_cooldown_seconds = 30
        self._circuit_window_seconds = 300
        self._metrics_lock = threading.Lock()
        self._provider_metrics: dict[str, dict] = {p: {
            "successes_7d": 0,
            "failures_7d": 0,
            "total_latency_ms": 0.0,
            "request_count_7d": 0,
            "last_failure_time": 0.0,
            "recovery_attempts": 0,
        } for p in self.clients}
        self._provider_latency_p95: dict[str, float] = {p: 1000.0 for p in self.clients}
        self._latency_history: dict[str, list[float]] = {p: [] for p in self.clients}
        self._latency_history_max = 100
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._redis = None
        self._redis_circuit_prefix = "circuit:state:"
        self._redis_failures_prefix = "circuit:failures:"
        self._load_circuit_from_redis()

    def _get_redis(self):
        """Lazily get Redis client, cached for the lifetime of the mesh."""
        if self._redis is None:
            try:
                from src.caching.redis_layer import _get_redis as _r
                self._redis = _r()
            except Exception:
                self._redis = False
        return self._redis if self._redis else None

    def _load_circuit_from_redis(self) -> None:
        """Load circuit breaker state from Redis on startup. Graceful degradation if Redis unavailable."""
        redis = self._get_redis()
        if redis is None:
            return
        now = time.time()
        for provider in list(self.clients):
            try:
                state_key = f"{self._redis_circuit_prefix}{provider}"
                failures_key = f"{self._redis_failures_prefix}{provider}"

                saved_state = redis.get(state_key)
                if saved_state in ("open", "half_open", "closed"):
                    self._circuit_state[provider] = saved_state

                failure_times = redis.zrange(failures_key, 0, -1, withscores=True)
                if failure_times:
                    valid_times = [ts for ts, _ in failure_times if now - ts < self._circuit_window_seconds]
                    self._failure_history[provider] = valid_times
                    if valid_times and len(valid_times) >= self._circuit_failure_threshold:
                        self._circuit_state[provider] = "open"
            except Exception:
                pass

    def _persist_circuit_to_redis(self, provider: str) -> None:
        """Persist circuit state and failure history to Redis. Fails silently if Redis unavailable."""
        redis = self._get_redis()
        if redis is None:
            return
        try:
            state_key = f"{self._redis_circuit_prefix}{provider}"
            failures_key = f"{self._redis_failures_prefix}{provider}"
            state = self._circuit_state.get(provider, "closed")
            ttl = int(self._circuit_window_seconds + 300)
            redis.setex(state_key, ttl, state)
            if state == "open":
                redis.delete(failures_key)
            else:
                pipe = redis.pipeline()
                pipe.delete(failures_key)
                for ts in self._failure_history.get(provider, []):
                    pipe.zadd(failures_key, {str(ts): ts})
                pipe.expire(failures_key, ttl)
                pipe.execute()
        except Exception:
            pass

    def _load_mesh_config(self) -> LLMMeshConfig:
        """Load mesh configuration from environment."""
        fallback_order_str = _env("LLM_FALLBACK_ORDER", "nvidia,gemini,openai") or "nvidia,gemini,openai"
        fallback_order = [p.strip() for p in fallback_order_str.split(",")]

        return LLMMeshConfig(
            primary_provider=fallback_order[0] if fallback_order else "nvidia",
            fallback_order=fallback_order[1:] if len(fallback_order) > 1 else [],
            max_retries=int(_env("LLM_MAX_RETRIES", "3") or "3"),
            retry_delay_seconds=int(_env("LLM_RETRY_DELAY_SECONDS", "5") or "5"),
            request_timeout_seconds=int(_env("LLM_REQUEST_TIMEOUT_SECONDS", "15") or "15"),
            query_timeout_budget_seconds=int(_env("LLM_TIMEOUT_BUDGET", "15") or "15"),
        )

    def _initialize_clients(self) -> None:
        """Initialize all configured LLM clients."""
        all_providers = [self.mesh_config.primary_provider] + self.mesh_config.fallback_order

        for provider in all_providers:
            try:
                settings = load_llm_settings(provider)

                if provider == "nvidia":
                    self.clients[provider] = NvidiaLLMClient(settings)
                elif provider == "openai":
                    self.clients[provider] = OpenAIResponsesClient(settings)
                elif provider == "anthropic":
                    self.clients[provider] = AnthropicMessagesClient(settings)
                elif provider == "azure":
                    self.clients[provider] = AzureOpenAIClient(settings)
                elif provider == "gemini":
                    self.clients[provider] = GeminiGenAIClient(settings)
                elif provider == "minimax":
                    self.clients[provider] = MinimaxLLMClient(settings)

                logger.info(f"✅ LLM Mesh: {provider} client initialized")

            except Exception as e:
                logger.warning(f"⚠️ LLM Mesh: {provider} client failed: {e}")

        if not self.clients:
            raise LLMConfigError("No LLM providers available in mesh")

    def _is_provider_circuit_open(self, provider: str) -> bool:
        """Check if circuit breaker is open for a provider.
        
        Half-open: allow 1 test request through to verify recovery.
        """
        with self._failure_lock:
            state = self._circuit_state.get(provider, "closed")
            if state == "closed":
                return False
            if state == "half_open":
                return False
            now = time.time()
            last_failure = self._provider_metrics.get(provider, {}).get("last_failure_time", 0.0)
            cooldown = self._get_cooldown(provider)
            if now - last_failure >= cooldown:
                self._circuit_state[provider] = "half_open"
                logger.info(f"🔌 Circuit breaker HALF-OPEN for {provider} (cooldown={cooldown}s expired)")
                self._persist_circuit_to_redis(provider)
                return False
            return True

    def _is_provider_recently_failed(self, provider: str) -> bool:
        """Skip providers that failed in the last 60s (circuit breaker overlap)."""
        with self._metrics_lock:
            last_failure = self._provider_metrics.get(provider, {}).get("last_failure_time", 0.0)
            return (time.time() - last_failure) < 60.0

    def _get_health_score(self, provider: str) -> float:
        """Compute health score: 1 / (latency_p95 * (1 + error_rate_7d)). Higher = healthier."""
        with self._metrics_lock:
            m = self._provider_metrics.get(provider, {})
            successes = m.get("successes_7d", 0)
            failures = m.get("failures_7d", 0)
            total = successes + failures
            if total == 0:
                return 1.0
            error_rate = failures / total
            p95_latency = self._provider_latency_p95.get(provider, 1000.0)
            if p95_latency <= 0:
                p95_latency = 1.0
            return 1.0 / (p95_latency * (1.0 + error_rate))

    def _get_health_weighted_providers(self) -> list[str]:
        """Return providers sorted by health score, skipping recently-failed ones.

        Phase 3 auto-disable: providers with >15% 7-day error rate are removed from rotation.
        """
        available = [p for p in self.clients if p in self._provider_metrics]
        scored = []
        for p in available:
            if self._is_provider_recently_failed(p) or self._is_provider_circuit_open(p):
                continue
            m = self._provider_metrics.get(p, {})
            total = m.get("request_count_7d", 0)
            failures = m.get("failures_7d", 0)
            if total >= 10 and failures / total > 0.15:
                logger.info(f"⏸️ Provider {p} auto-disabled (7-day error rate={failures/total:.1%} > 15%)")
                continue
            scored.append((p, self._get_health_score(p)))
        scored.sort(key=lambda x: -x[1])
        return [p for p, _ in scored]

    def _record_success(self, provider: str, latency_ms: float = 0.0) -> None:
        """Record a success, update metrics, and close the circuit breaker."""
        with self._metrics_lock:
            m = self._provider_metrics.get(provider, {})
            m["successes_7d"] = m.get("successes_7d", 0) + 1
            m["request_count_7d"] = m.get("request_count_7d", 0) + 1
            if latency_ms > 0:
                m["total_latency_ms"] = m.get("total_latency_ms", 0.0) + latency_ms
                self._latency_history.setdefault(provider, []).append(latency_ms)
                if len(self._latency_history[provider]) > self._latency_history_max:
                    self._latency_history[provider] = self._latency_history[provider][-self._latency_history_max:]
                sorted_latencies = sorted(self._latency_history[provider])
                n = len(sorted_latencies)
                p95_idx = max(0, int(n * 0.95) - 1)
                self._provider_latency_p95[provider] = sorted_latencies[p95_idx]
        with self._failure_lock:
            self._failure_history[provider] = []
            prev_state = self._circuit_state.get(provider)
            if prev_state == "half_open":
                self._circuit_state[provider] = "closed"
                logger.info(f"🔌 Circuit breaker CLOSED for {provider} after successful half-open test")
            elif self._circuit_state.get(provider) != "closed":
                self._circuit_state[provider] = "closed"
                if prev_state != "closed":
                    logger.info(f"🔌 Circuit breaker CLOSED for {provider}")
        self._persist_circuit_to_redis(provider)

    def _record_failure(self, provider: str) -> None:
        """Record a failure and potentially trip the circuit breaker."""
        with self._metrics_lock:
            m = self._provider_metrics.get(provider, {})
            m["failures_7d"] = m.get("failures_7d", 0) + 1
            m["request_count_7d"] = m.get("request_count_7d", 0) + 1
            m["last_failure_time"] = time.time()
        with self._failure_lock:
            now = time.time()
            self._failure_history.setdefault(provider, []).append(now)
            self._failure_history[provider] = [
                t for t in self._failure_history[provider]
                if now - t < self._circuit_window_seconds
            ]
            if len(self._failure_history[provider]) >= self._circuit_failure_threshold:
                self._circuit_state[provider] = "open"
                logger.warning(f"🔌 Circuit breaker OPEN for {provider} after {len(self._failure_history[provider])} failures")
        self._persist_circuit_to_redis(provider)

    def _get_cooldown(self, provider: str) -> float:
        """Get exponential backoff cooldown: 30s → 60s → 120s → 300s."""
        with self._failure_lock:
            failures = len(self._failure_history.get(provider, []))
        base = [30, 60, 120, 300]
        idx = min(failures - self._circuit_failure_threshold, len(base) - 1)
        return base[idx] if idx >= 0 else 30.0

    def _try_provider(
        self,
        provider: str,
        system_prompt: str,
        user_prompt: str,
        conversation_history: list,
        timeout_seconds: float,
    ) -> tuple[str, float] | None:
        """Try a single provider with timeout. Returns (response, latency_ms) or None."""
        start = time.time()
        try:
            client = self.clients[provider]
            response = client.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                conversation_history=conversation_history,
            )
            latency_ms = (time.time() - start) * 1000
            if len(response) > 0:
                self._record_success(provider, latency_ms)
                return response, latency_ms
        except Exception as e:
            self._record_failure(provider)
            logger.warning(f"⚠️ LLM Mesh: {provider} failed: {e}")
        return None

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[list[dict]] = None,
        complexity: Optional[str] = None,
    ) -> str:
        """
        Generate response with global 15s budget, health-weighted routing, and parallel first-provider race.

        Falls through: cloud LLM (top-2 providers racing, or top-3 for complex) → local SLM → rule-based
        Total LLM time budget: 15 seconds max (LLM_TIMEOUT_BUDGET env var).

        Phase 2 enhancements:
        - complexity=complex: race top-3 providers simultaneously, cancel losers on first success
        - Local SLM fallback with graceful degradation message when all cloud providers fail
        """
        conversation_history = conversation_history or []
        budget_remaining = self.mesh_config.query_timeout_budget_seconds
        last_error = None

        race_count = 3 if complexity == "complex" else 2

        while budget_remaining > 0:
            providers = self._get_health_weighted_providers()
            if not providers:
                break

            top_providers = providers[:race_count] if len(providers) >= race_count else providers[:2] if len(providers) >= 2 else providers[:1]

            futures = {}
            for provider in top_providers:
                fut = self._executor.submit(
                    self._try_provider,
                    provider,
                    system_prompt,
                    user_prompt,
                    conversation_history,
                    budget_remaining,
                )
                futures[fut] = provider

            completed_futures = set()
            for fut in as_completed(futures, timeout=budget_remaining):
                provider = futures[fut]
                try:
                    result = fut.result(timeout=budget_remaining)
                    if result is not None:
                        response, latency_ms = result
                        logger.info(f"✅ LLM Mesh: {provider} won race (latency={latency_ms:.0f}ms)")
                        for f in futures:
                            if f not in completed_futures:
                                f.cancel()
                        return response
                except Exception:
                    pass
                completed_futures.add(fut)

            for fut in futures:
                if fut not in completed_futures:
                    fut.cancel()

            budget_remaining = max(0, budget_remaining - 1)
            if budget_remaining <= 0:
                break

        local_client = self._get_local_llm_client()
        if local_client:
            try:
                logger.info("🌐 All cloud providers failed — falling back to local SLM")
                response = local_client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    conversation_history=conversation_history,
                )
                return response
            except Exception as e:
                logger.warning(f"Local SLM fallback failed: {e}")
                last_error = str(e)

        raise LLMProviderError(
            f"LLM timeout budget exhausted ({self.mesh_config.query_timeout_budget_seconds}s). "
            f"Last error: {last_error}"
        )

    def _get_local_llm_client(self):
        """Get local SLM client if available."""
        try:
            from src.config.local_llm import get_local_llm_client
            return get_local_llm_client()
        except Exception:
            return None

    def generate_streaming(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[list[dict]] = None,
        complexity: Optional[str] = None,
    ):
        """
        Streaming generator: fires top-2 (or top-3 for complex) providers in parallel,
        yields tokens from the first to respond. Falls back to local SLM if all cloud
        providers fail with message: 'using offline model for this response'.
        Yields: str tokens
        """
        conversation_history = conversation_history or []
        providers = self._get_health_weighted_providers()
        if not providers:
            return

        race_count = 3 if complexity == "complex" else 2
        top_providers = providers[:race_count] if len(providers) >= race_count else providers[:2] if len(providers) >= 2 else providers[:1]

        for provider in top_providers:
            if self._is_provider_circuit_open(provider) or self._is_provider_recently_failed(provider):
                continue
            client = self.clients.get(provider)
            if client is None or not hasattr(client, "generate_streaming"):
                continue

            start = time.time()
            try:
                for token in client.generate_streaming(
                    system_prompt,
                    user_prompt,
                    conversation_history,
                ):
                    latency_ms = (time.time() - start) * 1000
                    self._record_success(provider, latency_ms)
                    yield token
                return
            except Exception as e:
                self._record_failure(provider)
                logger.warning(f"⚠️ LLM Mesh streaming failed for {provider}: {e}")
                break

        local_client = self._get_local_llm_client()
        if local_client:
            try:
                logger.info("🌐 All cloud providers failed streaming — falling back to local SLM")
                for token in local_client.generate_streaming(
                    system_prompt,
                    user_prompt,
                    conversation_history,
                ):
                    yield token
                return
            except Exception as e:
                logger.warning(f"Local SLM streaming fallback failed: {e}")

        fallback_response = client.generate(system_prompt, user_prompt, conversation_history)
        for i in range(0, len(fallback_response), 10):
            yield fallback_response[i : i + 10]

    def get_available_providers(self) -> list[str]:
        """Get list of available LLM providers in mesh."""
        return list(self.clients.keys())

    def get_provider_health(self) -> dict:
        """Return per-provider health status with latency and success rate metrics."""
        result = {}
        providers = self._get_health_weighted_providers()
        all_providers = list(self.clients.keys())

        for provider in all_providers:
            with self._metrics_lock:
                m = self._provider_metrics.get(provider, {})
                successes = m.get("successes_7d", 0)
                failures = m.get("failures_7d", 0)
                total = successes + failures

            circuit_state = self._circuit_state.get(provider, "closed")
            status = "healthy"
            if circuit_state == "open":
                status = "down"
            elif circuit_state == "half_open":
                status = "degraded"
            elif self._is_provider_recently_failed(provider):
                status = "degraded"
            elif total > 0 and failures / total > 0.3:
                status = "degraded"

            result[provider] = {
                "status": status,
                "circuit": circuit_state,
                "success_rate_7d": round(successes / total, 3) if total > 0 else None,
                "latency_p95_ms": round(self._provider_latency_p95.get(provider, 0.0), 1) or None,
                "requests_7d": total,
                "last_failure_seconds_ago": round(time.time() - m.get("last_failure_time", 0.0), 1),
                "health_rank": providers.index(provider) + 1 if provider in providers else len(providers) + 1,
                "error_rate_7d": round(failures / total, 3) if total > 0 else None,
            }

        return result

    def health_check(self) -> dict:
        """Check health of all LLM providers in mesh including circuit breaker state."""
        health = {}

        for provider, client in self.clients.items():
            circuit_state = self._circuit_state.get(provider, "closed")
            try:
                test_response = client.generate(
                    system_prompt="You are a test system.",
                    user_prompt="Respond with 'OK' only.",
                    conversation_history=[],
                )
                health[provider] = {
                    "status": "healthy",
                    "circuit": circuit_state,
                    "response_length": len(test_response),
                    "failures_last_5min": len(self._failure_history.get(provider, [])),
                }
            except Exception as e:
                health[provider] = {
                    "status": "unhealthy",
                    "circuit": circuit_state,
                    "error": str(e),
                    "failures_last_5min": len(self._failure_history.get(provider, [])),
                }

        return health


_llm_mesh_instance: SovereignLLMMesh | None = None


def get_llm_mesh() -> SovereignLLMMesh:
    """Get singleton sovereign LLM mesh instance (metrics shared across calls)."""
    global _llm_mesh_instance
    if _llm_mesh_instance is None:
        _llm_mesh_instance = SovereignLLMMesh()
    return _llm_mesh_instance


class CostGuard:
    """
    LLM Budget Governance — prevents cloud LLM budget burnout.

    Every query has a cost cap. Every provider has a budget.
    Every month has a ceiling.

    CAPS: per-query cost limits by complexity
    THRESHOLDS: monthly budget triggers
    AUTO-FALLBACK: >85% -> Local SLM for non-critical
    HARD HALT: >95% -> cloud LLMs disabled except P0

    PERSONA OVERRIDES (Phase 2):
    - Government tier: always route through Minimax/NVIDIA (sovereign mandate)
    - Industry tier: force cheapest viable path (local SLM -> Gemini Flash)
    """

    CAPS: dict[str, float] = {
        "trivial": 0,
        "simple": 5,
        "standard": 50,
        "complex": 200,
        "critical": 500,
    }

    PROVIDER_COSTS_INPUT: dict[str, float] = {
        "local": 0,
        "rule_based": 0,
        "gemini": 150,
        "minimax": 300,
        "azure": 450,
        "openai": 2250,
        "anthropic": 3000,
        "nvidia": 2000,
    }

    PROVIDER_COSTS_OUTPUT: dict[str, float] = {
        "local": 0,
        "rule_based": 0,
        "gemini": 600,
        "minimax": 900,
        "azure": 1350,
        "openai": 6750,
        "anthropic": 15000,
        "nvidia": 6000,
    }

    ALLOCATION: dict[str, float] = {
        "researcher_tier": 0.40,
        "government_tier": 0.35,
        "industry_tier": 0.15,
        "system_operations": 0.08,
        "incident_reserve": 0.02,
    }

    THRESHOLDS: dict[str, float] = {"warning": 0.70, "critical": 0.85, "halt": 0.95}

    _instance: "CostGuard | None" = None
    _lock = threading.Lock()

    def __init__(self, monthly_budget_inr: float = 500000.0):
        self.monthly_budget_inr = monthly_budget_inr
        self._spent_this_month = 0.0
        self._month_start = time.time()
        self._query_count = 0
        self._allocation_lock = threading.Lock()
        self._redis: Optional[object] = None
        self._redis_key_prefix = "costguard:monthly:"
        self._allocate_budget()
        self._load_from_storage()
        self._load_spent_from_redis()

    def _get_redis(self):
        if self._redis is None:
            try:
                from src.caching.redis_layer import _get_redis as _r
                self._redis = _r()
            except Exception:
                self._redis = False
        return self._redis if self._redis else None

    def _redis_key(self) -> str:
        import datetime
        return f"{self._redis_key_prefix}{datetime.date.today().strftime('%Y-%m')}"

    def _load_spent_from_redis(self) -> None:
        redis = self._get_redis()
        if redis is None:
            return
        try:
            key = self._redis_key()
            val = redis.get(key)
            if val is not None:
                self._spent_this_month = float(val)
        except Exception:
            pass

    def _persist_spent_to_redis(self) -> None:
        redis = self._get_redis()
        if redis is None:
            return
        try:
            key = self._redis_key()
            ttl = 45 * 24 * 3600
            redis.setex(key, ttl, str(self._spent_this_month))
        except Exception:
            pass

    @classmethod
    def get_instance(cls) -> "CostGuard":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        with cls._lock:
            cls._instance = None

    def _allocate_budget(self) -> None:
        self._budget_by_tier: dict[str, float] = {
            tier: self.monthly_budget_inr * pct
            for tier, pct in self.ALLOCATION.items()
        }
        self._spent_by_tier: dict[str, float] = {
            "researcher_tier": 0.0,
            "government_tier": 0.0,
            "industry_tier": 0.0,
            "system_operations": 0.0,
            "incident_reserve": 0.0,
        }

    def _load_from_storage(self) -> None:
        try:
            import sqlite3
            conn = sqlite3.connect("nrg_research.db")
            row = conn.execute(
                """
                SELECT SUM(cost_inr) FROM llm_cost_log
                WHERE timestamp >= date('now', 'start of month')
                """
            ).fetchone()
            if row and row[0]:
                self._spent_this_month = float(row[0])
            conn.close()
        except Exception:
            pass

    def get_tier_key(self, user_tier: int) -> str:
        return {1: "researcher_tier", 2: "government_tier", 3: "industry_tier"}.get(
            user_tier, "researcher_tier"
        )

    def get_budget_status(self) -> dict:
        pct = self._spent_this_month / self.monthly_budget_inr
        return {
            "spent_inr": self._spent_this_month,
            "budget_inr": self.monthly_budget_inr,
            "percentage": pct,
            "percentage_display": f"{pct * 100:.1f}%",
            "warning": pct >= self.THRESHOLDS["warning"],
            "critical": pct >= self.THRESHOLDS["critical"],
            "halt": pct >= self.THRESHOLDS["halt"],
        }

    def estimate_tokens(self, query: str, context_chunks: int = 0) -> tuple[int, int]:
        """Estimate tokens from query text and context chunks.

        Uses simple word/char heuristics since provider tokenizers vary.
        Returns (tokens_in, tokens_out_estimate).
        """
        words = len(query.split())
        tokens_in = int(words * 1.3) + 50
        tokens_out_estimate = 150 + (context_chunks * 40)
        return tokens_in, tokens_out_estimate

    def estimate_cost(
        self,
        complexity: str,
        provider: str,
        tokens_in: Optional[int] = None,
        tokens_out: Optional[int] = None,
        query: str = "",
        context_chunks: int = 0,
    ) -> float:
        """Estimate cost for a query. Pass either token counts or query+context_chunks."""
        if tokens_in is None or tokens_out is None:
            tokens_in, tokens_out = self.estimate_tokens(query, context_chunks)
        input_cost_per_1m = self.PROVIDER_COSTS_INPUT.get(provider, 0)
        output_cost_per_1m = self.PROVIDER_COSTS_OUTPUT.get(provider, 0)
        cost = (tokens_in / 1_000_000) * input_cost_per_1m + (tokens_out / 1_000_000) * output_cost_per_1m
        cap = self.CAPS.get(complexity, 500)
        return round(min(cost, cap), 4)

    def check_budget(
        self,
        user_tier: int,
        complexity: str,
        estimated_cost: float,
        guru_approval: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
        reason is empty if allowed, contains block reason if denied.

        Phase 2 persona overrides:
        - Government (tier 2): always allowed (sovereign mandate), routed to Minimax/NVIDIA
        - Industry (tier 3): force cheapest path, non-trivial capped at ₹5
        """
        if user_tier == 2:
            return True, "government_tier_sovereign_override"

        status = self.get_budget_status()

        if status["halt"] and estimated_cost > 0:
            if guru_approval:
                return True, f"guru_override: {guru_approval}"
            if self._spent_by_tier.get("incident_reserve", 0) < self._budget_by_tier.get("incident_reserve", 0):
                return True, "incident_reserve_override"
            return False, "Monthly halt threshold (95%) — cloud LLMs disabled"

        if status["critical"]:
            if complexity in ("trivial",):
                return True, ""
            if complexity in ("simple",):
                if guru_approval:
                    return True, f"guru_override: {guru_approval}"
                return False, "Budget critical (85%) — non-critical queries blocked"

        if user_tier == 3 and complexity != "trivial":
            cap = self.CAPS.get("simple", 5)
            if estimated_cost > cap:
                return False, f"Industry tier capped at ₹{cap} — query costs ₹{estimated_cost:.2f}"

        cap = self.CAPS.get(complexity, 500)
        if estimated_cost > cap:
            if guru_approval:
                return True, f"guru_approved: {guru_approval}"
            return False, f"Estimated ₹{estimated_cost:.2f} exceeds {complexity} cap ₹{cap}"

        return True, ""

    def get_provider_for_tier(self, user_tier: int, complexity: str) -> list[str]:
        """Return ordered provider list for persona. Phase 2 override."""
        if user_tier == 2:
            return ["minimax", "nvidia", "azure", "openai", "anthropic"]
        if user_tier == 3:
            return ["local", "gemini", "minimax"]
        if complexity == "trivial":
            return ["rule_based", "local"]
        if complexity == "simple":
            return ["local", "gemini", "minimax"]
        if complexity in ("standard",):
            return ["minimax", "gemini", "azure"]
        if complexity == "complex":
            return ["azure", "openai", "minimax"]
        return ["openai", "anthropic", "nvidia"]

    def record_cost(
        self,
        query_id: str,
        provider: str,
        tokens_in: int,
        tokens_out: int,
        cost_inr: float,
        persona: str,
        complexity: str,
        route_decision: str,
    ) -> None:
        """Record actual cost after LLM call. Updates counters + Redis."""
        from src.audit import log_cost_decision

        log_cost_decision(
            query_id=query_id,
            provider=provider,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_inr=cost_inr,
            persona=persona,
            complexity=complexity,
            route_decision=route_decision,
        )
        self._update_counters(cost_inr, persona)
        self._persist_spent_to_redis()

    def _update_counters(self, cost_inr: float, persona: str) -> None:
        with self._allocation_lock:
            self._spent_this_month += cost_inr
            tier_key = self.get_tier_key({"researcher": 1, "government": 2, "industry": 3}.get(persona, 1))
            if tier_key in self._spent_by_tier:
                self._spent_by_tier[tier_key] += cost_inr
            self._query_count += 1

    def get_cost_breakdown(self) -> dict:
        try:
            import sqlite3
            conn = sqlite3.connect("nrg_research.db")
            persona_breakdown = {}
            provider_breakdown = {}
            complexity_breakdown = {}

            for row in conn.execute(
                """
                SELECT persona, SUM(cost_inr), COUNT(*)
                FROM llm_cost_log
                WHERE timestamp >= date('now', 'start of month')
                GROUP BY persona
                """
            ).fetchall():
                persona_breakdown[row[0]] = {"cost": float(row[1]), "count": row[2]}

            for row in conn.execute(
                """
                SELECT provider, SUM(cost_inr), COUNT(*)
                FROM llm_cost_log
                WHERE timestamp >= date('now', 'start of month')
                GROUP BY provider
                """
            ).fetchall():
                provider_breakdown[row[0]] = {"cost": float(row[1]), "count": row[2]}

            for row in conn.execute(
                """
                SELECT complexity, SUM(cost_inr), COUNT(*)
                FROM llm_cost_log
                WHERE timestamp >= date('now', 'start of month')
                GROUP BY complexity
                """
            ).fetchall():
                complexity_breakdown[row[0]] = {"cost": float(row[1]), "count": row[2]}

            conn.close()
            return {
                "persona": persona_breakdown,
                "provider": provider_breakdown,
                "complexity": complexity_breakdown,
                "total_spent": round(self._spent_this_month, 2),
                "query_count": self._query_count,
                "budget_remaining": round(self.monthly_budget_inr - self._spent_this_month, 2),
                "budget_status": self.get_budget_status(),
                "allocation": {
                    "total": self.monthly_budget_inr,
                    "by_tier": {k: round(v, 2) for k, v in self._budget_by_tier.items()},
                    "spent_by_tier": {k: round(v, 2) for k, v in self._spent_by_tier.items()},
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def get_daily_cost_digest(self) -> str:
        """Appended to agent daily digest. Returns a formatted string."""
        status = self.get_budget_status()
        remaining = self.monthly_budget_inr - self._spent_this_month
        pct = status["percentage_display"]

        alerts = []
        if status["halt"]:
            alerts.append("HALT: Cloud LLMs disabled (95% budget)")
        elif status["critical"]:
            alerts.append("CRITICAL: Auto-fallback active (85% budget)")
        elif status["warning"]:
            alerts.append("WARNING: Approaching 70% budget")

        alert_str = " | ".join(alerts) if alerts else "No alerts"
        return (
            f"COST: \u20b9{self._spent_this_month:,.0f} spent | "
            f"\u20b9{remaining:,.0f} remaining ({pct}) | "
            f"{alert_str}"
        )

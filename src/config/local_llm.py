"""Local SLM (Small Language Model) integration for sovereign synthesis.

Primary: Llama.cpp HTTP server (GGUF Q4_K_M quantization)
Fallback: HuggingFace transformers with Phi-2 or rule-based templates
"""

import os
import logging
import time
from typing import Optional, List

import httpx

logger = logging.getLogger(__name__)

# Global model cache
_model = None
_tokenizer = None


def get_local_llm():
    """Get or initialize local LLM."""
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        # Use Phi-2 (2.7B parameters) - small but capable
        model_name = os.getenv("LOCAL_LLM_MODEL", "microsoft/phi-2")

        logger.info(f"Loading local LLM: {model_name}")

        # Load tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )

        # Load model with optimizations
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            device_map="auto",  # Auto-detect CPU/GPU
            trust_remote_code=True,
        )

        logger.info("Local LLM loaded successfully")
        return _model, _tokenizer

    except ImportError as e:
        logger.warning(f"transformers/torch not installed: {e}")
        return None, None
    except Exception as e:
        logger.error(f"Failed to load local LLM: {e}")
        return None, None


class LocalLLMClient:
    """Local LLM client that mimics cloud LLM interface."""

    def __init__(self):
        self.model, self.tokenizer = get_local_llm()
        self.max_length = int(os.getenv("LOCAL_LLM_MAX_LENGTH", "512"))

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Generate response using local model."""
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Local LLM not available")

        try:
            import torch

            # Build prompt
            prompt = self._build_prompt(system_prompt, user_prompt, conversation_history)

            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")

            # Move to same device as model
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=256,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            # Decode
            response: str = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the generated part (after the prompt)
            if prompt in response:
                response = response[len(prompt):].strip()

            return response

        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            raise

    def _build_prompt(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: Optional[List[dict]] = None,
    ) -> str:
        """Build prompt for local LLM."""
        parts = []

        # Add system prompt
        if system_prompt:
            parts.append(f"System: {system_prompt}")
            parts.append("")

        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-3:]:  # Last 3 turns
                if turn.get("query"):
                    parts.append(f"User: {turn['query']}")
                if turn.get("response"):
                    parts.append(f"Assistant: {turn['response']}")

        # Add current user prompt
        parts.append(f"User: {user_prompt}")
        parts.append("Assistant:")

        return "\n".join(parts)


def get_local_llm_client():
    """Get the configured local synthesis client.

    llama.cpp is the Phase 1 local path. HuggingFace Phi loading is retained
    only as an explicit developer opt-in because it is slow and fragile on CPU.
    """
    llama_client = get_llama_cpp_client()
    if llama_client is not None:
        return llama_client

    if os.getenv("LOCAL_LLM_ENABLE_HF", "false").lower() != "true":
        logger.info("No healthy llama.cpp server; skipping HuggingFace local model")
        return None

    client = LocalLLMClient()
    if client.model is not None:
        return client
    return None


class LlamaCppClient:
    """HTTP client for llama.cpp server (GGUF quantized models).

    Preferred for synthesis: runs locally, raw content never leaves VPC.
    """

    def __init__(self, url: str | None = None, model: str = "local"):
        self.url = url or os.getenv("LLAMA_CPP_URL", "http://localhost:8080")
        self.model = model
        self.timeout = float(os.getenv("LLAMA_CPP_TIMEOUT", "120"))

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        conversation_history: List[dict] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> str:
        """Generate response via llama.cpp HTTP API."""
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for turn in conversation_history[-5:]:
                if turn.get("query"):
                    messages.append({"role": "user", "content": turn["query"]})
                if turn.get("response"):
                    messages.append({"role": "assistant", "content": turn["response"]})

        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            response = httpx.post(
                f"{self.url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            choices = result.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content")
                if content:
                    return str(content)

            raise RuntimeError("llama.cpp response did not include content")

        except httpx.ConnectError:
            logger.warning("llama.cpp server not reachable at %s", self.url)
            raise RuntimeError(f"llama.cpp server not available at {self.url}")
        except httpx.TimeoutException:
            logger.warning("llama.cpp request timed out after %s seconds", self.timeout)
            raise RuntimeError(f"llama.cpp request timed out after {self.timeout}s")
        except Exception as e:
            logger.error("llama.cpp request failed: %s", e)
            raise

    def health_check(self) -> bool:
        """Check if llama.cpp server is healthy."""
        try:
            response = httpx.get(f"{self.url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


# Cache health check results to avoid repeated HTTP calls.
_llama_cpp_health_cache: tuple[float, bool] | None = None
_LLAMA_CACHE_TTL_SECONDS = 30.0


def get_llama_cpp_client() -> Optional[LlamaCppClient]:
    """Get LlamaCppClient if server is available (health-check cached, TTL 30s)."""
    global _llama_cpp_health_cache
    now = time.time()

    if _llama_cpp_health_cache is not None:
        cached_at, was_healthy = _llama_cpp_health_cache
        if now - cached_at < _LLAMA_CACHE_TTL_SECONDS:
            if was_healthy:
                return LlamaCppClient()
            return None
        # Cache expired; fall through to re-check

    try:
        client = LlamaCppClient()
        if client.health_check():
            _llama_cpp_health_cache = (now, True)
            return client
        logger.warning("llama.cpp server not healthy")
        _llama_cpp_health_cache = (now, False)
        return None
    except Exception as e:
        logger.warning("Failed to create LlamaCppClient: %s", e)
        _llama_cpp_health_cache = (now, False)
        return None


# Simple rule-based synthesis as ultimate fallback
def rule_based_synthesis(
    query: str,
    sql_results: list,
    chunks: list,
    user_tier: int,
) -> str:
    """Generate synthesis using rule-based templates.

    This is used when both cloud LLM and local SLM are unavailable.
    """
    lines = []

    # Header
    lines.append("# Research Intelligence Report")
    lines.append("")
    lines.append(f"**Query:** {query}")
    lines.append("")

    # Executive summary based on data
    if sql_results:
        lines.append("## Summary")
        lines.append(f"Found **{len(sql_results)}** research records matching your query.")
        lines.append("")

        # Group by research area
        areas: dict[str, int] = {}
        states: dict[str, int] = {}
        institutions: dict[str, int] = {}

        for row in sql_results:
            if isinstance(row, dict):
                area = row.get('research_area')
                if area:
                    areas[area] = areas.get(area, 0) + 1

                state = row.get('state')
                if state:
                    states[state] = states.get(state, 0) + 1

                inst = row.get('institution_id')
                if inst:
                    institutions[inst] = institutions.get(inst, 0) + 1

        if areas:
            lines.append("### Research Areas")
            for area, count in sorted(areas.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"- {area}: {count} researchers")
            lines.append("")

        if states:
            lines.append("### Geographic Distribution")
            for state, count in sorted(states.items(), key=lambda x: -x[1])[:5]:
                lines.append(f"- {state}: {count} researchers")
            lines.append("")

        # List top researchers
        lines.append("## Top Researchers")
        for i, row in enumerate(sql_results[:10], 1):
            if isinstance(row, dict):
                name = row.get('name', 'Unknown')
                area = row.get('research_area', 'N/A')
                state = row.get('state', 'N/A')
                lines.append(f"{i}. **{name}** - {area} ({state})")
        lines.append("")

    elif chunks:
        lines.append("## Document Analysis")
        lines.append(f"Found **{len(chunks)}** relevant document excerpts.")
        lines.append("")
        for i, chunk in enumerate(chunks[:5], 1):
            lines.append(f"{i}. {chunk[:150]}...")
            lines.append("")

    else:
        lines.append("No data found for this query.")

    # Tier-specific footer
    lines.append("")
    lines.append("---")
    if user_tier == 1:
        lines.append("*Researcher Tier Access: Full details shown with contact information.*")
    elif user_tier == 2:
        lines.append("*Government Tier Access: Aggregated and anonymized data shown.*")
    elif user_tier == 3:
        lines.append("*Industry Tier Access: Limited licensed data shown.*")

    return "\n".join(lines)

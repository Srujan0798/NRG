#!/usr/bin/env python3
"""Minimal local LLM server using llama-cpp-python.

Exposes OpenAI-compatible /v1/chat/completions and /health endpoints.
Matches the interface expected by src.config.local_llm.LlamaCppClient.
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import uvicorn

# Model configuration
MODEL_PATH = os.getenv("LOCAL_LLM_MODEL_PATH", "models/gemma-2b-it-q4_k_m.gguf")
N_CTX = int(os.getenv("LOCAL_LLM_N_CTX", "4096"))
N_GPU_LAYERS = int(os.getenv("LOCAL_LLM_N_GPU_LAYERS", "-1"))

_llm = None


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "local"
    messages: List[Message]
    temperature: float = 0.3
    max_tokens: int = 1024
    stream: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _llm
    try:
        from llama_cpp import Llama
        print(f"[local-llm] Loading model from {MODEL_PATH} ...", flush=True)
        _llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )
        print(f"[local-llm] Model loaded. Context={N_CTX}, GPU layers={N_GPU_LAYERS}", flush=True)
    except Exception as exc:
        print(f"[local-llm] Failed to load model: {exc}", flush=True)
        raise
    yield
    print("[local-llm] Shutting down.", flush=True)


app = FastAPI(title="NRG Local LLM", lifespan=lifespan)


@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": _llm is not None}


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    if _llm is None:
        return {"error": "Model not loaded"}, 503

    prompt_parts = []
    for msg in req.messages:
        if msg.role == "system":
            prompt_parts.append(f"System: {msg.content}")
        elif msg.role == "user":
            prompt_parts.append(f"User: {msg.content}")
        elif msg.role == "assistant":
            prompt_parts.append(f"Assistant: {msg.content}")
    prompt_parts.append("Assistant:")
    prompt = "\n".join(prompt_parts)

    output = _llm(
        prompt,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        stop=["User:", "System:"],
    )

    generated_text = output["choices"][0]["text"].strip()

    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": generated_text,
                },
                "finish_reason": "stop",
            }
        ],
        "model": req.model,
    }


def daemonize():
    """Double-fork to properly daemonize on Unix."""
    import os
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #1 failed: {e}\n")
        sys.exit(1)

    os.chdir(str(Path(__file__).resolve().parents[1]))
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"Fork #2 failed: {e}\n")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()

    import io
    log_path = Path("logs/local_llm.log")
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a+") as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemonize()
    uvicorn.run(app, host="0.0.0.0", port=8080)

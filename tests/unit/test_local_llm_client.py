import src.config.local_llm as local_llm


class HealthyLlamaClient:
    def health_check(self):
        return True


class UnhealthyLlamaClient:
    def health_check(self):
        return False


def test_get_local_llm_client_prefers_llama_cpp(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_ENABLE_HF", raising=False)
    monkeypatch.setattr(local_llm, "LlamaCppClient", lambda: HealthyLlamaClient())

    assert isinstance(local_llm.get_local_llm_client(), HealthyLlamaClient)


def test_get_local_llm_client_skips_hf_loader_by_default(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_ENABLE_HF", raising=False)
    monkeypatch.setattr(local_llm, "LlamaCppClient", lambda: UnhealthyLlamaClient())

    def fail_if_called():
        raise AssertionError("HuggingFace local model should be opt-in")

    monkeypatch.setattr(local_llm, "get_local_llm", fail_if_called)

    assert local_llm.get_local_llm_client() is None

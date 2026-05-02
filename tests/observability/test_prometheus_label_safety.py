from prometheus_client import REGISTRY, generate_latest

from src.observability import metrics


def test_prometheus_label_values_redact_direct_identifiers():
    raw_email = "batch6.metrics.user@example.in"
    raw_pan = "ABCDE1234F"
    raw_phone = "+91 9876543210"

    metrics.count_query(1, raw_email, "success")
    metrics.count_llm_tokens("answer", "local", raw_pan, 1)
    metrics.count_rate_limited(raw_phone)  # type: ignore[arg-type]

    rendered = generate_latest(REGISTRY).decode("utf-8")

    assert raw_email not in rendered
    assert raw_pan not in rendered
    assert raw_phone not in rendered
    assert "redacted_pii" in rendered

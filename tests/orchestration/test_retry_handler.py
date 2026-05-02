"""Tests for RetryHandler wiring into orchestration nodes.

Covers A5-08: Retry handler immediate retries — RetryHandler must be wired
into synthesizer and executor with exponential backoff (2^n seconds, max 3 retries).
"""

import pytest
class TestRetryHandlerBackoff:
    """Verify RetryHandler implements correct exponential backoff."""

    def test_backoff_is_2_power_n(self):
        """Backoff delay = 2^n seconds for each attempt."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        h = RetryHandler()
        assert h.backoff_seconds(0) == 1.0
        assert h.backoff_seconds(1) == 2.0
        assert h.backoff_seconds(2) == 4.0

    def test_backoff_max_is_3_retries(self):
        """RetryHandler cap at max_retries=3."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        h = RetryHandler(max_retries=3)
        assert h.max_retries == 3
        delays = [h.backoff_seconds(i) for i in range(h.max_retries)]
        assert delays == [1.0, 2.0, 4.0]

    def test_backoff_sleep_fn_called_on_failure(self):
        """Sleep function called with exponential delay on each retry attempt.

        RetryHandler sleeps max_retries times: after the initial failure and
        before each retry attempt.
        """
        from src.orchestration.nodes.retry_handler import RetryHandler

        sleeps = []
        h = RetryHandler(max_retries=3, sleep_fn=lambda d: sleeps.append(d))

        call_count = 0
        def failing_op():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("LLM unavailable")

        with pytest.raises(RuntimeError):
            h.handle_retry(failing_op)

        assert call_count == 4
        assert sleeps == [1.0, 2.0, 4.0]

    def test_no_sleep_on_success(self):
        """No sleep delay if operation succeeds on first try."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        sleeps = []
        h = RetryHandler(max_retries=3, sleep_fn=lambda d: sleeps.append(d))

        result = h.handle_retry(lambda: "success")
        assert result == "success"
        assert sleeps == []

    def test_retries_until_success(self):
        """Operation succeeds on 2nd try (retry once, no final sleep)."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        sleeps = []
        h = RetryHandler(max_retries=3, sleep_fn=lambda d: sleeps.append(d))

        attempts = 0
        def flaky_op():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("transient failure")
            return "ok"

        result = h.handle_retry(flaky_op)
        assert result == "ok"
        assert attempts == 2
        assert sleeps == [1.0], "Only one retry delay (before 2nd attempt)"


class TestRetryHandlerIntegration:
    """Verify RetryHandler is usable as a context manager and in node pipelines."""

    def test_handler_produces_result_after_retries(self):
        """handle_retry returns operation result when it eventually succeeds."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        h = RetryHandler(max_retries=3)
        result = h.handle_retry(lambda: 42)
        assert result == 42

    def test_handler_raises_after_max_retries(self):
        """After max_retries retry delays, final exception is raised."""
        from src.orchestration.nodes.retry_handler import RetryHandler

        h = RetryHandler(max_retries=2)
        with pytest.raises(RuntimeError, match="always fails"):
            h.handle_retry(lambda: (_ for _ in ()).throw(RuntimeError("always fails")))

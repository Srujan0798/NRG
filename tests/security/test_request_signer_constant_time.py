"""Request signature verification hardening regressions."""

import time
from unittest.mock import patch

from src.security.request_signer import RequestSigner


def test_malformed_signature_still_uses_fixed_length_compare_digest():
    signer = RequestSigner(secret="test-secret")

    with patch("src.security.request_signer.hmac.compare_digest", return_value=False) as compare_digest:
        valid, reason = signer.verify("{}", int(time.time()), "abc")

    assert valid is False
    assert reason == "Malformed signature"
    compared_expected, compared_candidate = compare_digest.call_args.args
    assert len(compared_expected) == 64
    assert len(compared_candidate) == 64

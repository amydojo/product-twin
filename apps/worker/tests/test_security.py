import time

from product_twin.security import ReplayGuard, sign, verify


def test_hmac_roundtrip() -> None:
    timestamp = str(int(time.time()))
    nonce = "nonce-value-1234567890"
    signature = sign("POST", "/internal/jobs/1/start", timestamp, nonce, b"", "x" * 32)
    assert verify(
        "POST",
        "/internal/jobs/1/start",
        timestamp,
        nonce,
        b"",
        signature,
        "x" * 32,
    )


def test_rejects_tampering_stale_requests_and_short_secrets() -> None:
    timestamp = str(int(time.time()))
    nonce = "nonce-value-1234567890"
    signature = sign("POST", "/x", timestamp, nonce, b"a", "x" * 32)
    assert not verify("POST", "/x", timestamp, nonce, b"b", signature, "x" * 32)
    assert not verify("POST", "/x", "1", nonce, b"a", signature, "x" * 32)
    assert not verify("POST", "/x", timestamp, nonce, b"a", signature, "short")


def test_replay_guard_accepts_each_nonce_once_until_expiry() -> None:
    guard = ReplayGuard(ttl_seconds=5)
    nonce = "nonce-value-1234567890"
    assert guard.accept(nonce, now=100)
    assert not guard.accept(nonce, now=101)
    assert guard.accept(nonce, now=106)

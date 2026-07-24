import hashlib
import hmac
import re
import threading
import time

_NONCE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


def sign(method: str, path: str, timestamp: str, nonce: str, body: bytes, secret: str) -> str:
    payload = b"\n".join(
        [
            method.upper().encode(),
            path.encode(),
            timestamp.encode(),
            nonce.encode(),
            hashlib.sha256(body).hexdigest().encode(),
        ]
    )
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify(
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body: bytes,
    signature: str,
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    if len(secret) < 32 or not _NONCE_PATTERN.fullmatch(nonce):
        return False
    try:
        if abs(time.time() - int(timestamp)) > max_age_seconds:
            return False
    except ValueError:
        return False
    return hmac.compare_digest(
        sign(method, path, timestamp, nonce, body, secret),
        signature,
    )


class ReplayGuard:
    def __init__(self, ttl_seconds: int = 300, max_entries: int = 10_000) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._expires: dict[str, float] = {}
        self._lock = threading.Lock()

    def accept(self, nonce: str, now: float | None = None) -> bool:
        if not _NONCE_PATTERN.fullmatch(nonce):
            return False
        current = time.time() if now is None else now
        with self._lock:
            self._expires = {
                value: expiry
                for value, expiry in self._expires.items()
                if expiry > current
            }
            if nonce in self._expires:
                return False
            if len(self._expires) >= self.max_entries:
                oldest = min(self._expires, key=self._expires.__getitem__)
                del self._expires[oldest]
            self._expires[nonce] = current + self.ttl_seconds
        return True

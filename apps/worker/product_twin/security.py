import hashlib
import hmac
import time


def sign(method: str, path: str, timestamp: str, body: bytes, secret: str) -> str:
    payload = b"\n".join(
        [
            method.upper().encode(),
            path.encode(),
            timestamp.encode(),
            hashlib.sha256(body).hexdigest().encode(),
        ]
    )
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def verify(
    method: str,
    path: str,
    timestamp: str,
    body: bytes,
    signature: str,
    secret: str,
    max_age_seconds: int = 300,
) -> bool:
    try:
        if abs(time.time() - int(timestamp)) > max_age_seconds:
            return False
    except ValueError:
        return False
    return hmac.compare_digest(
        sign(method, path, timestamp, body, secret),
        signature,
    )

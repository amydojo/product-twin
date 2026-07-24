import time

from fastapi.testclient import TestClient

from product_twin.api import app
from product_twin.security import sign
from product_twin.settings import settings


def test_worker_start_rejects_a_replayed_valid_request(monkeypatch) -> None:
    secret = "worker-test-secret-with-at-least-32-bytes"
    timestamp = str(int(time.time()))
    nonce = "api-replay-test-nonce-0001"
    path = "/internal/jobs/00000000-0000-4000-8000-000000000123/start"
    signature = sign("POST", path, timestamp, nonce, b"", secret)
    headers = {
        "x-product-twin-nonce": nonce,
        "x-product-twin-timestamp": timestamp,
        "x-product-twin-signature": signature,
    }
    monkeypatch.setattr(settings, "product_twin_internal_secret", secret)
    monkeypatch.setattr(settings, "product_twin_fixture_mode", True)

    with TestClient(app) as client:
        first = client.post(path, headers=headers)
        replay = client.post(path, headers=headers)

    assert first.status_code == 202
    assert first.json()["mode"] == "fixture"
    assert replay.status_code == 409

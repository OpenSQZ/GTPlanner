import json
import pytest
from fastapi.testclient import TestClient

import fastapi_main as app_module


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    # enable auth + rate limit: 3 req per 30s
    monkeypatch.setenv("GTPLANNER_SECURITY_ENABLE_API_KEY_AUTH", "true")
    monkeypatch.setenv("GTPLANNER_SECURITY_API_KEYS", json.dumps(["tenantA-rl"]))
    monkeypatch.setenv("GTPLANNER_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("GTPLANNER_RATE_LIMIT_WINDOW_SECONDS", "30")
    monkeypatch.setenv("GTPLANNER_RATE_LIMIT_MAX_REQUESTS", "3")
    monkeypatch.setenv("GTPLANNER_RATE_LIMIT_PER_TENANT", "true")
    yield


def get_client():
    return TestClient(app_module.app)


def test_rate_limit_exceeded():
    client = get_client()
    headers = {"X-API-Key": "tenantA-rl"}
    payload = {
        "session_id": "s1",
        "dialogue_history": [{"role": "user", "content": "hi"}],
    }
    # fire 3 requests (allowed)
    for _ in range(3):
        r = client.post("/api/chat/agent", json=payload, headers=headers)
        assert r.status_code != 401 and r.status_code != 403
    # 4th should be 429
    r = client.post("/api/chat/agent", json=payload, headers=headers)
    assert r.status_code == 429



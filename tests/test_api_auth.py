import os
import json
import pytest
from fastapi.testclient import TestClient

import fastapi_main as app_module


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("GTPLANNER_SECURITY_ENABLE_API_KEY_AUTH", "true")
    monkeypatch.setenv("GTPLANNER_SECURITY_API_KEYS", json.dumps(["tenantA-xxxx"]))
    # reload module-level configs if necessary
    yield


def get_client():
    return TestClient(app_module.app)


def test_chat_agent_unauthorized():
    client = get_client()
    payload = {
        "session_id": "s1",
        "dialogue_history": [{"role": "user", "content": "hi"}],
    }
    r = client.post("/api/chat/agent", json=payload)
    assert r.status_code in (401, 403)


def test_chat_agent_authorized():
    client = get_client()
    payload = {
        "session_id": "s1",
        "dialogue_history": [{"role": "user", "content": "hi"}],
    }
    headers = {"X-API-Key": "tenantA-xxxx"}
    # We only assert it's not 401/403; actual SSE stream may hang in tests, so expect either 200 or 500 in CI
    r = client.post("/api/chat/agent", json=payload, headers=headers, timeout=5)
    assert r.status_code != 401 and r.status_code != 403



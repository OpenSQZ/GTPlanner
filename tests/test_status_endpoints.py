from fastapi.testclient import TestClient
import fastapi_main as app_module


def get_client():
    return TestClient(app_module.app)


def test_health_and_status():
    client = get_client()
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert "api_status" in j
    assert "auth_enabled" in j
    assert "rate_limit_enabled" in j
    assert "tool_index_ready" in j
    assert "llm_probe" in j

    r2 = client.get("/api/status")
    assert r2.status_code == 200
    s = r2.json()
    assert "rate_limit" in s and "sse" in s


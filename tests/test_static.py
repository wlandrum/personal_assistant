from fastapi.testclient import TestClient
import assistant.server as server


def test_index_is_served():
    client = TestClient(server.app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Assistant" in r.text


def test_health_still_works():
    client = TestClient(server.app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True

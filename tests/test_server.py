import uuid
import hashlib
import secrets
from fastapi.testclient import TestClient

import assistant.server as server
from assistant.data.store import UserStore


def make_user(conn, name):
    cur = conn.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (name,))
    return str(cur.fetchone()[0])


def mint(conn, owner_id):
    token = secrets.token_urlsafe(16)
    h = hashlib.sha256(token.encode()).hexdigest()
    conn.execute("INSERT INTO api_tokens (owner_id, token_hash) VALUES (%s, %s)", (owner_id, h))
    return token


class FakeOrch:
    def __init__(self):
        self.seen = None

    def respond(self, owner_id, message, history=None):
        self.seen = (owner_id, message)
        return f"echo:{message}"


def setup_module(_):
    server.orch = FakeOrch()


def test_message_requires_token():
    client = TestClient(server.app)
    r = client.post("/message", json={"message": "hi"})
    assert r.status_code == 401


def test_invalid_token_rejected():
    client = TestClient(server.app)
    r = client.post("/message", json={"message": "hi"}, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_valid_token_resolves_owner_and_replies():
    u = make_user(server.conn, f"u_{uuid.uuid4()}")
    token = mint(server.conn, u)
    client = TestClient(server.app)
    r = client.post("/message", json={"message": "hello"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["reply"] == "echo:hello"
    assert server.orch.seen[0] == u

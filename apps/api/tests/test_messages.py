# apps/api/tests/test_messages.py
from fastapi.testclient import TestClient


def test_list_messages_empty(client: TestClient):
    assert client.get("/api/messages").json() == []


def test_create_message_returns_201(client: TestClient):
    response = client.post("/api/messages", json={"text": "Hello", "author": "Alice"})
    assert response.status_code == 201


def test_create_message_response_body(client: TestClient):
    body = client.post("/api/messages", json={"text": "Hello", "author": "Alice"}).json()
    assert body["text"] == "Hello"
    assert body["author"] == "Alice"
    assert "id" in body


def test_create_message_default_author(client: TestClient):
    body = client.post("/api/messages", json={"text": "No author"}).json()
    assert body["author"] == "Anonyme"


def test_create_message_empty_text_returns_400(client: TestClient):
    response = client.post("/api/messages", json={"text": "   ", "author": "Alice"})
    assert response.status_code == 400


def test_list_messages_after_create(client: TestClient):
    client.post("/api/messages", json={"text": "First", "author": "Bob"})
    client.post("/api/messages", json={"text": "Second", "author": "Bob"})
    messages = client.get("/api/messages").json()
    assert len(messages) == 2
    assert messages[0]["text"] == "First"


def test_create_message_id_is_unique(client: TestClient):
    r1 = client.post("/api/messages", json={"text": "A", "author": "X"})
    r2 = client.post("/api/messages", json={"text": "B", "author": "X"})
    assert r1.json()["id"] != r2.json()["id"]

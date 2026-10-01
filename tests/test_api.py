import pytest
from fastapi.testclient import TestClient

from demo_api.main import create_app

KEY = "test-only-credential-" + "a" * 32
OTHER = "test-only-credential-" + "b" * 32


@pytest.fixture
def client():
    with TestClient(create_app({"local": KEY, "ci": OTHER})) as client:
        client.headers["X-API-Key"] = KEY
        yield client


def test_crud_filters_and_isolation(client):
    payload = {"name": "Angel Demo", "email": "angel@example.com", "role": "sales"}
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    path = response.headers["Location"]
    assert client.get(path).json()["email"] == payload["email"]
    assert client.post("/users", json=payload).status_code == 409
    assert client.get("/users?role=sales&limit=1").json()["total"] == 1
    assert client.get(path, headers={"X-API-Key": OTHER}).status_code == 404
    assert client.patch(path, json={"active": False}).json()["active"] is False
    assert client.get("/users?active=false").json()["total"] == 1
    assert (
        client.put(path, json={"name": "Updated", "email": "new@example.com"}).json()["active"]
        is True
    )
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_auth_validation_and_docs(client):
    assert client.get("/users", headers={"X-API-Key": "wrong"}).status_code == 401
    client.headers.pop("X-API-Key")
    assert client.get("/users").status_code == 401
    assert client.get("/health").status_code == 200
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert schema["components"]["securitySchemes"]["APIKeyHeader"]["name"] == "X-API-Key"
    client.headers["X-API-Key"] = KEY
    assert client.post("/users", json={"name": "", "email": "invalid"}).status_code == 422
    assert client.get("/users?limit=0").status_code == 422
    assert client.get("/users/not-a-uuid").status_code == 422
    created = client.post("/users", json={"name": "A", "email": "a@example.com"}).json()
    assert client.patch(f"/users/{created['id']}", json={"name": None}).status_code == 422


def test_restart_restores_seed_and_missing_config_fails():
    with pytest.raises(RuntimeError):
        create_app({})
    with TestClient(create_app({"local": KEY})) as client:
        assert client.get("/users", headers={"X-API-Key": KEY}).json()["total"] == 1

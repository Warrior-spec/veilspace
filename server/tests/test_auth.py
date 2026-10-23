from contextlib import closing
import time

from fastapi.testclient import TestClient
import pytest

from veilspace.config import Settings
from veilspace.database import connect_database
from veilspace.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        yield client


def register(client, email="person@example.com"):
    response = client.post("/api/auth/register", json={
        "email": email, "display_name": "Test Member", "password": "DocumentDemo2026!"
    })
    assert response.status_code == 201, response.text
    return response.json()


def headers(session):
    return {"Authorization": "Bearer " + session["access_token"]}


def test_users_are_distinct_and_logout_revokes_only_one_session(client):
    first = register(client)
    second = register(client, "second@example.com")
    assert first["user"]["id"] != second["user"]["id"]
    assert client.get("/api/auth/me", headers=headers(first)).json() == first["user"]
    assert client.get("/api/auth/me", headers=headers(second)).json() == second["user"]
    assert client.post("/api/auth/logout", headers=headers(first)).status_code == 204
    assert client.get("/api/auth/me", headers=headers(first)).status_code == 401
    assert client.get("/api/auth/me", headers=headers(second)).status_code == 200


def test_passwords_and_tokens_are_not_stored_in_plaintext(client):
    session = register(client)
    with closing(connect_database(client.app.state.settings.data_dir)) as connection:
        password = connection.execute("SELECT password_hash FROM users").fetchone()[0]
        token = connection.execute("SELECT token_hash FROM sessions").fetchone()[0]
        assert password.startswith("scrypt$")
        assert "DocumentDemo2026!" not in password
        assert token != session["access_token"]
        assert len(token) == 64


def test_email_normalization_and_duplicate_registration(client):
    register(client, " Member@Example.com ")
    response = client.post("/api/auth/register", json={
        "email": "member@example.com", "display_name": "Another Member", "password": "DocumentDemo2026!"
    })
    assert response.status_code == 409
    response = client.post("/api/auth/login", json={
        "email": "MEMBER@example.com", "password": "DocumentDemo2026!"
    })
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "member@example.com"


def test_invalid_credentials_and_missing_token(client):
    register(client)
    responses = [client.post("/api/auth/login", json={"email": email, "password": "wrong"})
                 for email in ["person@example.com", "absent@example.com"]]
    assert all(response.status_code == 401 for response in responses)
    assert responses[0].json() == responses[1].json()
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer made-up"}).status_code == 401


def test_expired_session_is_rejected(client):
    session = register(client)
    with closing(connect_database(client.app.state.settings.data_dir)) as connection:
        with connection:
            connection.execute("UPDATE sessions SET expires_at=?", (int(time.time()) - 1,))
    assert client.get("/api/auth/me", headers=headers(session)).status_code == 401


def test_sessions_survive_server_restart(tmp_path):
    settings = Settings(data_dir=tmp_path)
    with TestClient(create_app(settings)) as first:
        session = register(first)
    with TestClient(create_app(settings)) as second:
        assert second.get("/api/auth/me", headers=headers(session)).status_code == 200


def test_closed_registration_and_input_validation(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path, allow_registration=False))) as client:
        response = client.post("/api/auth/register", json={
            "email": "person@example.com", "display_name": "Member", "password": "DocumentDemo2026!"
        })
        assert response.status_code == 403
        response = client.post("/api/auth/register", json={
            "email": "not-an-email", "display_name": "Member", "password": "short"
        })
        assert response.status_code == 422


def test_login_attempts_are_limited(client):
    for _ in range(20):
        response = client.post("/api/auth/login", json={"email": "absent@example.com", "password": "wrong"})
        assert response.status_code == 401
    assert client.post("/api/auth/login", json={"email": "absent@example.com", "password": "wrong"}).status_code == 429

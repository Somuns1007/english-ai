"""Isolated authentication tests; only temporary databases are created."""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

from auth import service
from auth.router import router

SECRET = "test-only-secret-with-at-least-32-bytes"
ACCOUNT = {"email": "Student@example.com", "password": "safe-password-123"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("AUTH_JWT_SECRET", SECRET)
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    app = FastAPI()
    app.include_router(router)
    with TestClient(app, base_url="https://testserver", headers={"X-Auth-Request": "1"}) as client:
        yield client


def test_register_login_me_logout(client):
    assert client.get("/api/auth/me").status_code == 401
    created = client.post("/api/auth/register", json=ACCOUNT)
    assert created.status_code == 201
    assert created.json()["email"] == "student@example.com"
    assert "password_hash" not in created.json()
    assert client.get("/api/auth/me").status_code == 401
    logged = client.post("/api/auth/login", json=ACCOUNT)
    assert logged.status_code == 200
    assert "token" not in logged.json()
    cookie = logged.headers["set-cookie"]
    for flag in ("HttpOnly", "Secure", "SameSite=lax", "Max-Age=2592000", "Path=/"):
        assert flag in cookie
    claims = jwt.decode(client.cookies["token"], SECRET, algorithms=["HS256"], audience=service.ISSUER)
    assert claims["exp"] - claims["iat"] == service.TOKEN_SECONDS
    assert client.get("/api/auth/me").json() == created.json()
    assert client.get("/api/auth/me").headers["cache-control"] == "no-store"
    out = client.post("/api/auth/logout")
    assert out.status_code == 204
    assert "Max-Age=0" in out.headers["set-cookie"]
    assert client.get("/api/auth/me").status_code == 401


def test_duplicate_and_wrong_password(client):
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 201
    assert client.post("/api/auth/register", json={**ACCOUNT, "email": " student@EXAMPLE.com "}).status_code == 409
    for email in (ACCOUNT["email"], "missing@example.com"):
        result = client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
        assert result.status_code == 401
        assert result.json()["detail"] == "邮箱或密码错误"


@pytest.mark.parametrize("data", [
    {**ACCOUNT, "email": "bad-email"}, {**ACCOUNT, "password": "short"},
    {**ACCOUNT, "password": "a" * 73}, {**ACCOUNT, "password": "中" * 25}, {},
])
def test_invalid_input(client, data):
    assert client.post("/api/auth/register", json=data).status_code == 422


def test_hash_and_inactive_user(client):
    client.post("/api/auth/register", json=ACCOUNT)
    client.post("/api/auth/login", json=ACCOUNT)
    with service.database() as db:
        row = db.execute("SELECT * FROM users").fetchone()
        assert row["password_hash"].startswith("$2b$")
        assert ACCOUNT["password"] not in row["password_hash"]
        db.execute("UPDATE users SET is_active = 0")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json=ACCOUNT).status_code == 401


@pytest.mark.parametrize("kind", ["expired", "invalid", "no_exp", "wrong_algorithm"])
def test_bad_tokens(client, kind):
    user = client.post("/api/auth/register", json=ACCOUNT).json()
    claims = {"sub": user["id"], "iat": datetime.now(timezone.utc), "iss": service.ISSUER,
              "aud": service.ISSUER, "exp": datetime.now(timezone.utc) + timedelta(days=1)}
    if kind == "expired": claims["exp"] = datetime.now(timezone.utc) - timedelta(days=1)
    if kind == "no_exp": del claims["exp"]
    token = jwt.encode(claims, SECRET, algorithm="HS512" if kind == "wrong_algorithm" else "HS256")
    client.cookies.set("token", "broken-token" if kind == "invalid" else token)
    assert client.get("/api/auth/me").status_code == 401


def test_csrf_guard(client):
    assert client.post("/api/auth/register", json=ACCOUNT, headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/api/auth/logout", headers={"X-Auth-Request": ""}).status_code == 403
    assert client.post("/api/auth/register", json=ACCOUNT, headers={"Origin": "http://localhost:5173"}).status_code == 201


def test_missing_secret_fails_before_db_write(client, monkeypatch, tmp_path):
    monkeypatch.delenv("AUTH_JWT_SECRET")
    assert client.post("/api/auth/register", json=ACCOUNT).status_code == 503
    assert not (tmp_path / "auth.db").exists()


def test_listening_path_rejected(monkeypatch):
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "listening" / "data" / "listening.db"
    monkeypatch.setenv("AUTH_DB_PATH", str(path))
    with pytest.raises(RuntimeError):
        with service.database():
            pass

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models import BrowserSession


def test_login_uses_persistent_opaque_cookie_and_logout_revokes_it(
    client: TestClient, login
) -> None:
    login()
    set_cookie = client.post(
        "/api/sesion/login",
        json={"username": "operadora", "password": "helado-seguro"},
    ).headers["set-cookie"]
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Max-Age=2592000" in set_cookie
    cookie = client.cookies.get("heladeria_session")
    assert cookie is not None
    assert client.get("/api/sesion/actual").json()["username"] == "operadora"

    logout = client.post("/api/sesion/logout")
    assert logout.status_code == 204
    assert client.get("/api/sesion/actual").status_code == 401


def test_login_rotates_the_previous_session(client: TestClient) -> None:
    credentials = {"username": "operadora", "password": "helado-seguro"}
    assert client.post("/api/sesion/login", json=credentials).status_code == 204
    old_token = client.cookies.get("heladeria_session")

    assert client.post("/api/sesion/login", json=credentials).status_code == 204
    assert client.cookies.get("heladeria_session") != old_token

    old_browser = TestClient(
        client.app,
        base_url="https://testserver",
        headers={"Origin": "https://testserver"},
        cookies={"heladeria_session": old_token},
    )
    assert old_browser.get("/api/sesion/actual").status_code == 401


def test_expired_session_is_rejected_and_removed(
    client: TestClient, login, session_factory: sessionmaker[Session]
) -> None:
    login()
    with session_factory() as db:
        browser_session = db.scalar(select(BrowserSession))
        assert browser_session is not None
        browser_session.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    assert client.get("/api/sesion/actual").status_code == 401
    with session_factory() as db:
        assert db.scalar(select(BrowserSession)) is None


def test_invalid_credentials_are_generic(client: TestClient) -> None:
    response = client.post(
        "/api/sesion/login", json={"username": "nobody", "password": "wrong"}
    )
    assert response.status_code == 401
    assert response.json()["message"] == "El usuario o la contraseña son incorrectos."

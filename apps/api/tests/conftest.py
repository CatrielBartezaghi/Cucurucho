from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from datetime import UTC, datetime

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.main import create_app
from app.models import User
from app.storage import StoredImage


class FakeImageStorage:
    def __init__(self) -> None:
        self.images: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.fail_upload = False

    def upload(self, content: bytes, content_type: str) -> StoredImage:
        if self.fail_upload:
            raise RuntimeError("controlled upload failure")
        key = f"products/image-{len(self.images) + 1}"
        self.images[key] = content
        return StoredImage(key=key, url=f"https://images.test/{key}")

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.images.pop(key, None)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://heladeria:heladeria@db:5432/heladeria",
        ),
        direct_database_url=os.getenv(
            "TEST_DATABASE_URL",
            "postgresql+psycopg://heladeria:heladeria@db:5432/heladeria",
        ),
        app_origin="https://testserver",
        session_cookie_secure=True,
        argon2_time_cost=1,
        argon2_memory_cost=8192,
        argon2_parallelism=1,
    )


@pytest.fixture()
def image_storage() -> FakeImageStorage:
    return FakeImageStorage()


@pytest.fixture()
def session_factory(settings: Settings) -> Iterator[sessionmaker[Session]]:
    engine = create_engine(settings.database_url)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE sale_details, sales, browser_sessions, products, users "
                "RESTART IDENTITY CASCADE"
            )
        )
    with factory() as db:
        db.add(
            User(
                username="operadora",
                password_hash=PasswordHasher(
                    time_cost=settings.argon2_time_cost,
                    memory_cost=settings.argon2_memory_cost,
                    parallelism=settings.argon2_parallelism,
                ).hash("helado-seguro"),
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
    yield factory
    engine.dispose()


@pytest.fixture()
def client(
    settings: Settings,
    session_factory: sessionmaker[Session],
    image_storage: FakeImageStorage,
) -> Iterator[TestClient]:
    app = create_app(settings, session_factory, image_storage)
    with TestClient(
        app,
        base_url="https://testserver",
        headers={"Origin": "https://testserver"},
    ) as test_client:
        yield test_client


@pytest.fixture()
def login(client: TestClient) -> Callable[[], None]:
    def perform() -> None:
        response = client.post(
            "/api/sesion/login",
            json={"username": "operadora", "password": "helado-seguro"},
        )
        assert response.status_code == 204

    return perform


@pytest.fixture()
def product_factory(client: TestClient) -> Callable[[str, str], dict[str, object]]:
    def create(name: str, price: str) -> dict[str, object]:
        response = client.post("/api/productos", json={"name": name, "price": price})
        assert response.status_code == 201, response.text
        return response.json()

    return create

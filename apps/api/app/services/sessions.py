from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Never

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import hash_token, new_token
from ..config import Settings
from ..errors import ApiError
from ..models import BrowserSession, User


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    username: str


@dataclass(frozen=True)
class StartedSession:
    raw_token: str
    max_age_seconds: int


class Sessions:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._hasher = PasswordHasher(
            time_cost=settings.argon2_time_cost,
            memory_cost=settings.argon2_memory_cost,
            parallelism=settings.argon2_parallelism,
        )

    def authenticate(self, db: Session, username: str, password: str) -> StartedSession:
        user = db.scalar(select(User).where(User.username == username.strip()))
        valid = False
        if user is not None:
            try:
                valid = self._hasher.verify(user.password_hash, password)
            except VerifyMismatchError:
                pass
        if not valid or user is None:
            raise ApiError(
                401, "invalid_credentials", "El usuario o la contraseña son incorrectos."
            )

        db.execute(delete(BrowserSession).where(BrowserSession.user_id == user.id))
        raw_token = new_token()
        now = datetime.now(UTC)
        max_age = self._settings.session_days * 24 * 60 * 60
        db.add(
            BrowserSession(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                created_at=now,
                expires_at=now + timedelta(seconds=max_age),
            )
        )
        db.commit()
        return StartedSession(raw_token, max_age)

    def resolve(self, db: Session, raw_token: str | None) -> CurrentUser:
        if not raw_token:
            self._session_required()
        browser_session = db.scalar(
            select(BrowserSession).where(BrowserSession.token_hash == hash_token(raw_token))
        )
        if browser_session is None or browser_session.expires_at <= datetime.now(UTC):
            if browser_session is not None:
                db.delete(browser_session)
                db.commit()
            self._session_required()
        return CurrentUser(browser_session.user.id, browser_session.user.username)

    def revoke(self, db: Session, raw_token: str | None) -> None:
        if raw_token:
            db.execute(
                delete(BrowserSession).where(
                    BrowserSession.token_hash == hash_token(raw_token)
                )
            )
            db.commit()

    @staticmethod
    def _session_required() -> Never:
        raise ApiError(
            401,
            "session_required",
            "Tu sesión venció o fue revocada. Iniciá sesión nuevamente.",
        )

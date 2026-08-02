from __future__ import annotations

import argparse
import getpass
import os
from datetime import UTC, datetime

from argon2 import PasswordHasher
from sqlalchemy import select

from .config import get_settings
from .db import build_session_factory
from .models import User


def main() -> None:
    parser = argparse.ArgumentParser(description="Provisiona la única cuenta operativa.")
    parser.add_argument("username")
    args = parser.parse_args()
    password = os.getenv("PROVISION_PASSWORD") or getpass.getpass("Contraseña: ")
    confirmation = os.getenv("PROVISION_PASSWORD") or getpass.getpass("Repetir contraseña: ")
    if not password or password != confirmation:
        raise SystemExit("Las contraseñas no coinciden o están vacías.")

    settings = get_settings()
    hasher = PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )
    factory = build_session_factory(settings)
    with factory() as db:
        if db.scalar(select(User)) is not None:
            raise SystemExit("La cuenta operativa ya fue provisionada.")
        db.add(
            User(
                username=args.username.strip(),
                password_hash=hasher.hash(password),
                created_at=datetime.now(UTC),
            )
        )
        db.commit()
    print("Cuenta provisionada.")


if __name__ == "__main__":
    main()

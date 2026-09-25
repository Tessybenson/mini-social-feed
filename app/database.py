"""
Database setup for the Mini Social Media Feed app.

Connection info comes entirely from the DATABASE_URL environment variable,
with a fallback to the project .env file so local development works without
manual shell exports. Example (local Postgres):

    export DATABASE_URL="postgresql+psycopg2://postgres:password@localhost:5432/mini_social_feed"
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


def _load_env_file() -> None:
    """Populate os.environ from the project .env when DATABASE_URL is missing."""
    if os.environ.get("DATABASE_URL"):
        return

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file()
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Example: export DATABASE_URL='postgresql+psycopg2://user:pass@localhost:5432/mini_social_feed'"
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

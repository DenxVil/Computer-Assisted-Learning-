import os

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def sqlalchemy_database_url(value: str):
    """Normalize provider PostgreSQL URLs for the installed Psycopg 3 driver."""
    url = make_url(value)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    return url


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+psycopg://cal:cal@localhost:5432/cal"
)
engine = create_engine(
    sqlalchemy_database_url(DATABASE_URL),
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=5,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.env_config import load_project_env

load_project_env()

_engine = None
_session_factory = None


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def connect_to_db() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return _normalize_database_url(database_url)

    user = quote_plus(os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres")))
    password = quote_plus(
        os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "postgres"))
    )
    host = os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost"))
    port = os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))
    db = os.getenv("POSTGRES_DB", os.getenv("PGDATABASE", "nba_news_agent_db"))
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(connect_to_db(), pool_pre_ping=True)
    return _engine


def get_session():
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _session_factory()

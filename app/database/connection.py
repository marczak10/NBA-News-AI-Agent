import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.services.env_config import load_project_env

load_project_env()

_engine = None
_session_factory = None


def connect_to_db() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    user = os.getenv("SQLSERVER_USER", "sa")
    password = quote_plus(os.getenv("SQLSERVER_PASSWORD", "YourStrong!Passw0rd"))
    host = os.getenv("SQLSERVER_HOST", "localhost")
    port = os.getenv("SQLSERVER_PORT", "1433")
    db = os.getenv("SQLSERVER_DB", "nba_news_agent_db")
    return f"mssql+pymssql://{user}:{password}@{host}:{port}/{db}"


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

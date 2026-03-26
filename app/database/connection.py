from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()


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

engine = create_engine(connect_to_db(), pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()

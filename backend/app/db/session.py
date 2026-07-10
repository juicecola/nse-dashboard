"""
session.py
----------
Postgres connection setup. Reads from environment variables so the same
code works locally (docker-compose), in Airflow, and in the FastAPI app.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PG_USER = os.getenv("POSTGRES_USER", "nse_dashboard")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nse_dashboard")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "nse_dashboard")

DATABASE_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

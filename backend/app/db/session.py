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

# "prefer" works fine for local docker-compose Postgres (no SSL configured).
# Hosted providers that require TLS on external connections - Render, Neon,
# Supabase, etc. - need this set to "require" via the POSTGRES_SSLMODE env
# var (e.g. in a GitHub Actions secret), or psycopg2 will fail to connect.
PG_SSLMODE = os.getenv("POSTGRES_SSLMODE", "prefer")

DATABASE_URL = (
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    f"?sslmode={PG_SSLMODE}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
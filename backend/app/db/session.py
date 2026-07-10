"""
session.py
----------
Postgres connection setup. Reads from environment variables so the same
code works locally (docker-compose), in Airflow, and in the FastAPI app.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. Check if Render's single connection string is available
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render's URL starts with postgres://, but SQLAlchemy 2.0 requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    # 2. Fallback to your local Docker Compose / Individual Environment pieces
    PG_USER = os.getenv("POSTGRES_USER", "nse_dashboard")
    PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nse_dashboard")
    PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
    PG_PORT = os.getenv("POSTGRES_PORT", "5432")
    PG_DB = os.getenv("POSTGRES_DB", "nse_dashboard")
    
    DATABASE_URL = f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"

# `pool_pre_ping=True` is excellent here—it helps FastAPI gracefully recover 
# if Render puts your DB to sleep on the free tier.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
"""
Database configuration for HAQLOON.

Uses SQLite for zero-config local persistence. Swap SQLALCHEMY_DATABASE_URL
for a Postgres/MySQL DSN in production without touching the rest of the app.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./haqloon.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed only for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

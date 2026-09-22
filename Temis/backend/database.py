#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database configuration for TEMIS
Using SQLite with Google Drive Service Account persistence
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temis.db")
SQLITE_URL = f"sqlite:///{DB_PATH}"

# Connection string resolution
db_url_env = os.getenv("DATABASE_URL", "").strip()

# Always prioritize SQLite when migrating to Google Drive SA or when DATABASE_URL is dead/empty
if not db_url_env or "dpg-" in db_url_env or os.getenv("FORCE_SQLITE", "true").lower() in ("1", "true", "yes"):
    SQLALCHEMY_DATABASE_URL = SQLITE_URL
else:
    if db_url_env.startswith("postgres://"):
        db_url_env = db_url_env.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URL = db_url_env

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args
    )
    if not SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            pass
except Exception as e:
    print(f"[Database] Warning: Failed to connect to {SQLALCHEMY_DATABASE_URL}: {e}. Falling back to SQLite.")
    SQLALCHEMY_DATABASE_URL = SQLITE_URL
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

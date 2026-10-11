"""
database/connection.py

Database connection and session management for Module 2.

Responsibilities:
    - Load PostgreSQL configuration from environment variables
    - Build the database connection URL
    - Lazily create the SQLAlchemy engine
    - Provide database sessions for API/database operations
    - Check database connectivity safely

Supported configuration:

Option 1 - DATABASE_URL:
    DATABASE_URL=postgresql+psycopg2://user:password@host:5432/database

Option 2 - Individual variables:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=road_health_db
    DB_USER=postgres
    DB_PASSWORD=your_password

Never hardcode real database credentials in this file.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker


# ============================================================
# ENVIRONMENT CONFIGURATION
# ============================================================

# Load variables from .env if it exists.
# Environment variables already defined by the operating
# system take precedence.
load_dotenv()


# ============================================================
# GLOBAL DATABASE OBJECTS
# ============================================================

DATABASE_URL: Optional[str] = None

engine: Optional[Engine] = None

SessionLocal: Optional[sessionmaker] = None


# ============================================================
# DATABASE URL
# ============================================================

def _build_database_url() -> str:
    """
    Build the PostgreSQL SQLAlchemy connection URL.

    Priority:
        1. DATABASE_URL
        2. Individual DB_* environment variables

    Returns:
        str: PostgreSQL SQLAlchemy connection URL.

    Raises:
        RuntimeError:
            If the required database configuration is missing.
    """

    # --------------------------------------------------------
    # Option 1: DATABASE_URL
    # --------------------------------------------------------

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        database_url = database_url.strip()

        if not database_url:
            raise RuntimeError(
                "DATABASE_URL is empty. "
                "Set a valid PostgreSQL connection URL."
            )

        # Some hosting platforms provide:
        #
        # postgresql://...
        #
        # SQLAlchemy can work with the PostgreSQL dialect,
        # but explicitly using psycopg2 keeps the driver
        # consistent with requirements.txt.
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+psycopg2://",
                1,
            )

        return database_url

    # --------------------------------------------------------
    # Option 2: Individual DB_* variables
    # --------------------------------------------------------

    host = os.getenv("DB_HOST", "localhost").strip()
    port = os.getenv("DB_PORT", "5432").strip()
    name = os.getenv("DB_NAME", "road_health_db").strip()
    user = os.getenv("DB_USER", "postgres").strip()
    password = os.getenv("DB_PASSWORD")

    # --------------------------------------------------------
    # Validate required values
    # --------------------------------------------------------

    if not host:
        raise RuntimeError(
            "DB_HOST is empty. Set DB_HOST in your environment."
        )

    if not port:
        raise RuntimeError(
            "DB_PORT is empty. Set DB_PORT in your environment."
        )

    if not name:
        raise RuntimeError(
            "DB_NAME is empty. Set DB_NAME in your environment."
        )

    if not user:
        raise RuntimeError(
            "DB_USER is empty. Set DB_USER in your environment."
        )

    if password is None or not password.strip():
        raise RuntimeError(
            "No DATABASE_URL or DB_PASSWORD was provided. "
            "Copy .env.example to .env and configure your "
            "PostgreSQL credentials."
        )

    # --------------------------------------------------------
    # Build SQLAlchemy PostgreSQL URL
    # --------------------------------------------------------

    return (
        f"postgresql+psycopg2://"
        f"{user}:{password}@{host}:{port}/{name}"
    )


# ============================================================
# ENGINE INITIALIZATION
# ============================================================

def init_engine() -> Engine:
    """
    Lazily initialize and return the SQLAlchemy engine.

    The engine is created only when it is first needed.
    This prevents importing database.connection from
    immediately attempting a database connection.

    Returns:
        Engine: SQLAlchemy database engine.

    Raises:
        RuntimeError:
            If database configuration is invalid.
    """

    global DATABASE_URL
    global engine
    global SessionLocal

    # --------------------------------------------------------
    # Reuse existing engine
    # --------------------------------------------------------

    if engine is not None:
        return engine

    # --------------------------------------------------------
    # Build database URL
    # --------------------------------------------------------

    DATABASE_URL = _build_database_url()

    # --------------------------------------------------------
    # Create SQLAlchemy engine
    # --------------------------------------------------------

    engine = create_engine(
        DATABASE_URL,

        # Detect stale/dead connections before using them.
        pool_pre_ping=True,

        # Recycle connections periodically.
        # This helps avoid stale connections with some
        # PostgreSQL/network configurations.
        pool_recycle=1800,

        # Keep the connection pool reasonably small for
        # a student/local deployment.
        pool_size=5,

        max_overflow=10,

        # Do not echo SQL statements in normal operation.
        echo=False,
    )

    # --------------------------------------------------------
    # Create session factory
    # --------------------------------------------------------

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    return engine


# ============================================================
# DATABASE SESSION
# ============================================================

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Provide a database session with automatic transaction handling.

    Usage:

        with get_session() as session:
            session.execute(...)

    Behavior:
        - Creates a session
        - Yields the session
        - Commits if everything succeeds
        - Rolls back if an exception occurs
        - Always closes the session

    Raises:
        Exception:
            Re-raises database/application exceptions after
            rolling back the transaction.
    """

    init_engine()

    if SessionLocal is None:
        raise RuntimeError(
            "Database session factory was not initialized."
        )

    session: Session = SessionLocal()

    try:
        yield session

        # Commit the complete transaction.
        session.commit()

    except Exception:
        # Never leave a failed transaction open.
        session.rollback()
        raise

    finally:
        # Always release the connection/session.
        session.close()


# ============================================================
# DATABASE CONNECTION CHECK
# ============================================================

def check_connection() -> bool:
    """
    Check whether PostgreSQL is reachable.

    Returns:
        bool:
            True  -> database connection is successful.
            False -> database connection failed.

    This function never raises a database exception.
    """

    try:
        database_engine = init_engine()

        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception as exc:
        print(f"Database connection error: {exc}")
        return False


# ============================================================
# DATABASE ENGINE DISPOSAL
# ============================================================

def close_engine() -> None:
    """
    Dispose of the SQLAlchemy connection pool.

    Useful when shutting down the application or during tests.
    """

    global engine
    global SessionLocal
    global DATABASE_URL

    if engine is not None:
        engine.dispose()

    engine = None
    SessionLocal = None
    DATABASE_URL = None


# ============================================================
# MAIN - CONNECTION TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MODULE 2 — PostgreSQL Connection Test")
    print("=" * 60)

    try:
        if check_connection():
            print("PostgreSQL connection successful.")
        else:
            print("PostgreSQL connection failed.")

    except Exception as exc:
        print(f"Database configuration error: {exc}")

    finally:
        close_engine()

"""
Important

Do not put SQL table creation inside connection.py.

The responsibilities are now clean:

database/
├── connection.py   ← CONNECT to PostgreSQL
├── schema.sql      ← DEFINE tables/indexes/triggers
└── setup_db.py     ← CREATE database + APPLY schema

And your API does:

routes.py
   ↓
get_session()
   ↓
INSERT roads
   ↓
INSERT road_observations
   ↓
get observation_id
   ↓
INSERT road_health_predictions

So database/connection.py is now Done.
"""
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


load_dotenv(override=True)


def _build_database_url():
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5433")
    name = os.getenv("DB_NAME", "road_health_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD")

    if not password:
        raise RuntimeError("DB_PASSWORD is missing from .env")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=name,
    )


DATABASE_URL = _build_database_url()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@contextmanager
def get_session():
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return True

    except Exception as e:
        print(f"Database connection error: {e}")
        return False


if __name__ == "__main__":
    print("Checking PostgreSQL database connection...")

    if check_connection():
        print("PostgreSQL connection successful!")
    else:
        print("PostgreSQL connection failed!")
"""Database connection and utilities."""
import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator

# Get database configuration from environment
# Prefer individual env vars (set in docker-compose)
DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB", "autograph"),
    "user": os.getenv("POSTGRES_USER", "autograph"),
    "password": os.getenv("POSTGRES_PASSWORD", "autograph_dev_password"),
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": os.getenv("POSTGRES_PORT", "5432")
}


@contextmanager
def get_db_connection():
    """Get database connection context manager."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_db_cursor(dict_cursor: bool = True) -> Generator:
    """Get database cursor context manager."""
    with get_db_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()

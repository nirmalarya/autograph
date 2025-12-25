"""Database configuration and session management for diagram service."""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Try to import secrets manager (optional - falls back to env vars if not available)
try:
    from shared.python.secrets_manager import get_secret_or_env
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False
    # Fallback function
    def get_secret_or_env(secret_name, env_var, default=None):
        return os.getenv(env_var, default)

# Database URL - Try secrets manager first, fall back to environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "autograph")
POSTGRES_PASSWORD = get_secret_or_env("POSTGRES_PASSWORD", "POSTGRES_PASSWORD", "autograph_dev_password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "autograph")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create engine with connection pooling
# pool_size: number of connections to maintain in the pool
# max_overflow: number of connections to allow beyond pool_size
# pool_pre_ping: verify connection health before using from pool
# pool_recycle: recycle connections after this many seconds (prevents stale connections)
# pool_timeout: seconds to wait for connection from pool before giving up
engine = create_engine(
    DATABASE_URL,
    pool_size=10,              # Maintain 10 connections in the pool
    max_overflow=20,           # Allow 20 additional connections during high load
    pool_pre_ping=True,        # Verify connection health before using
    pool_recycle=3600,         # Recycle connections after 1 hour
    pool_timeout=30,           # Wait up to 30 seconds for a connection
    echo=False                 # Set to True for SQL query logging
)

# Query performance monitoring
SLOW_QUERY_THRESHOLD_MS = 100  # Log queries slower than 100ms

class QueryPerformanceMonitor:
    """Monitor database query performance and log slow queries."""

    @staticmethod
    def log_slow_query(query_text: str, duration_ms: float, explain_plan: str = None):
        """Log slow query with details."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "diagram-service",
            "level": "WARNING",
            "message": "Slow database query detected",
            "query_duration_ms": round(duration_ms, 2),
            "slow_query_threshold_ms": SLOW_QUERY_THRESHOLD_MS,
            "query": query_text[:500],  # Truncate long queries
        }

        if explain_plan:
            log_data["explain_plan"] = explain_plan

        print(json.dumps(log_data))

# SQLAlchemy event listeners for query performance monitoring
@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    conn.info.setdefault("query_start_time", []).append(time.time())

@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query duration and detect slow queries."""
    # Calculate query duration
    query_start_times = conn.info.get("query_start_time", [])
    if query_start_times:
        start_time = query_start_times.pop()
        duration_ms = (time.time() - start_time) * 1000

        # Log slow queries
        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            # Get EXPLAIN plan for slow SELECT queries
            explain_plan = None
            if statement.strip().upper().startswith('SELECT'):
                try:
                    # Execute EXPLAIN in a new transaction to avoid affecting current one
                    explain_result = conn.execute(text(f"EXPLAIN {statement}"))
                    explain_plan = "\n".join([row[0] for row in explain_result])
                except Exception:
                    # Ignore errors getting EXPLAIN plan
                    pass

            QueryPerformanceMonitor.log_slow_query(statement, duration_ms, explain_plan)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

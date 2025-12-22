"""Database configuration and session management for diagram service."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL
POSTGRES_USER = os.getenv("POSTGRES_USER", "autograph")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "autograph_dev_password")
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

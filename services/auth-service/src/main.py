"""Auth Service - User authentication and authorization."""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
import os
import traceback
import json
import logging
import signal
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import time
import time

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

from .database import get_db
from .models import User, RefreshToken, PasswordResetToken, AuditLog, EmailVerificationToken
import redis
import secrets
import pyotp
import qrcode
import io
import base64

load_dotenv()

# Redis configuration for token blacklist
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Initialize Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

# Configure structured logging
class StructuredLogger:
    """Structured logger with JSON output for distributed tracing."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        
        # Set log level from environment variable (default: INFO)
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
    
    def log(self, level: str, message: str, correlation_id: str = None, **kwargs):
        """Log structured message with correlation ID."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "level": level.upper(),
            "message": message,
            "correlation_id": correlation_id,
            **kwargs
        }
        
        # Use appropriate logging method based on level
        level_upper = level.upper()
        if level_upper == "DEBUG":
            self.logger.debug(json.dumps(log_data))
        elif level_upper == "WARNING":
            self.logger.warning(json.dumps(log_data))
        elif level_upper == "ERROR":
            self.logger.error(json.dumps(log_data))
        else:  # INFO or any other level
            self.logger.info(json.dumps(log_data))
    
    def debug(self, message: str, correlation_id: str = None, **kwargs):
        self.log("debug", message, correlation_id, **kwargs)
    
    def info(self, message: str, correlation_id: str = None, **kwargs):
        self.log("info", message, correlation_id, **kwargs)
    
    def error(self, message: str, correlation_id: str = None, exc: Exception = None, **kwargs):
        """Log error message with optional exception and stack trace."""
        if exc is not None:
            # Add exception details and stack trace
            kwargs['error_type'] = type(exc).__name__
            kwargs['error_message'] = str(exc)
            kwargs['stack_trace'] = traceback.format_exc()
        self.log("error", message, correlation_id, **kwargs)
    
    def exception(self, message: str, exc: Exception, correlation_id: str = None, **kwargs):
        """Log exception with full stack trace and context."""
        self.error(message, correlation_id=correlation_id, exc=exc, **kwargs)
    
    def warning(self, message: str, correlation_id: str = None, **kwargs):
        self.log("warning", message, correlation_id, **kwargs)

logger = StructuredLogger("auth-service")

# Prometheus metrics registry
registry = CollectorRegistry()

# Request metrics
request_count = Counter(
    'auth_service_requests_total',
    'Total number of requests',
    ['method', 'path', 'status_code'],
    registry=registry
)

request_duration = Histogram(
    'auth_service_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'path'],
    registry=registry
)

active_connections = Gauge(
    'auth_service_active_connections',
    'Number of active connections',
    registry=registry
)

# Authentication metrics
login_attempts = Counter(
    'auth_service_login_attempts_total',
    'Total login attempts',
    ['result'],  # success or failure
    registry=registry
)

registration_attempts = Counter(
    'auth_service_registration_attempts_total',
    'Total registration attempts',
    ['result'],  # success or failure
    registry=registry
)

token_issued = Counter(
    'auth_service_tokens_issued_total',
    'Total tokens issued',
    ['token_type'],  # access or refresh
    registry=registry
)

# Database metrics
database_queries = Counter(
    'auth_service_database_queries_total',
    'Total database queries',
    ['operation'],  # select, insert, update, delete
    registry=registry
)

database_query_duration = Histogram(
    'auth_service_database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    registry=registry
)

# Graceful shutdown state
class ShutdownState:
    """Track graceful shutdown state."""
    def __init__(self):
        self.is_shutting_down = False
        self.in_flight_requests = 0
    
    def increment_request(self):
        """Track incoming request."""
        if not self.is_shutting_down:
            self.in_flight_requests += 1
            return True
        return False
    
    def decrement_request(self):
        """Track completed request."""
        self.in_flight_requests = max(0, self.in_flight_requests - 1)
    
    def start_shutdown(self):
        """Signal shutdown has begun."""
        self.is_shutting_down = True
    
    def can_shutdown(self):
        """Check if safe to shutdown (no in-flight requests)."""
        return self.in_flight_requests == 0

shutdown_state = ShutdownState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Auth Service starting up")
    
    # Setup signal handlers for graceful shutdown
    def handle_shutdown(signum, frame):
        """Handle shutdown signals (SIGTERM, SIGINT)."""
        signal_name = signal.Signals(signum).name
        logger.info(
            "Shutdown signal received",
            signal=signal_name,
            in_flight_requests=shutdown_state.in_flight_requests
        )
        shutdown_state.start_shutdown()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
    
    logger.info("Auth Service started successfully")
    
    yield
    
    # Shutdown - wait for in-flight requests to complete
    logger.info(
        "Auth Service shutting down",
        in_flight_requests=shutdown_state.in_flight_requests
    )
    
    # Wait up to 30 seconds for in-flight requests to complete
    shutdown_timeout = 30
    waited = 0
    while not shutdown_state.can_shutdown() and waited < shutdown_timeout:
        logger.info(
            "Waiting for in-flight requests",
            in_flight_requests=shutdown_state.in_flight_requests,
            waited=waited
        )
        await asyncio.sleep(1)
        waited += 1
    
    if shutdown_state.in_flight_requests > 0:
        logger.warning(
            "Shutdown timeout reached with pending requests",
            in_flight_requests=shutdown_state.in_flight_requests
        )
    else:
        logger.info("All requests completed, shutting down cleanly")
    
    logger.info("Auth Service shutdown complete")

app = FastAPI(
    title="AutoGraph v3 Auth Service",
    description="Authentication and authorization service",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware to track metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics."""
    # Track active connections
    active_connections.inc()
    
    # Track request start time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Track request duration
        duration = time.time() - start_time
        request_duration.labels(
            method=request.method,
            path=request.url.path
        ).observe(duration)
        
        # Track request count
        request_count.labels(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code
        ).inc()
        
        return response
    finally:
        # Always decrement active connections
        active_connections.dec()

# Middleware to handle graceful shutdown
@app.middleware("http")
async def shutdown_middleware(request: Request, call_next):
    """Middleware to handle graceful shutdown - reject new requests and track in-flight."""
    # Check if shutting down
    if shutdown_state.is_shutting_down:
        logger.warning(
            "Request rejected - server shutting down",
            path=request.url.path,
            method=request.method
        )
        return JSONResponse(
            status_code=503,
            content={"detail": "Server is shutting down, please retry"}
        )
    
    # Track in-flight request
    if not shutdown_state.increment_request():
        return JSONResponse(
            status_code=503,
            content={"detail": "Server is shutting down, please retry"}
        )
    
    try:
        response = await call_next(request)
        return response
    finally:
        # Always decrement, even if error
        shutdown_state.decrement_request()

# Middleware to log correlation ID
@app.middleware("http")
async def log_correlation_id(request: Request, call_next):
    """Middleware to extract and log correlation ID."""
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    request.state.correlation_id = correlation_id
    
    logger.info(
        "Request received",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path
    )
    
    try:
        response = await call_next(request)
        logger.info(
            "Response sent",
            correlation_id=correlation_id,
            status_code=response.status_code
        )
        return response
    except Exception as e:
        logger.error(
            "Request processing error",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise

# Add exception handler for debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all exceptions and return detailed error."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    error_detail = {
        "error": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc()
    }
    logger.error(
        "Unhandled exception",
        correlation_id=correlation_id,
        error=str(exc),
        error_type=type(exc).__name__
    )
    return JSONResponse(
        status_code=500,
        content=error_detail
    )

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))


# Pydantic models with enhanced validation
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password meets minimum security requirements."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must not exceed 128 characters')
        # Note: Additional password requirements (uppercase, numbers, symbols)
        # can be enforced here if needed
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        """Validate full name has reasonable length."""
        if v is not None:
            if len(v) > 255:
                raise ValueError('Full name must not exceed 255 characters')
            # Remove leading/trailing whitespace
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_active: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# Helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    now = datetime.utcnow()
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "access"
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, db: Session, expires_days: int = None) -> tuple[str, str]:
    """Create JWT refresh token and save to database.
    
    Args:
        data: Token payload data
        db: Database session
        expires_days: Optional custom expiry in days (default: REFRESH_TOKEN_EXPIRE_DAYS)
    
    Returns:
        tuple: (encoded_jwt, jti) - The encoded token and its JWT ID
    """
    to_encode = data.copy()
    now = datetime.utcnow()
    
    # Use custom expiry if provided, otherwise use default
    if expires_days is None:
        expires_days = REFRESH_TOKEN_EXPIRE_DAYS
    expire = now + timedelta(days=expires_days)
    
    # Generate unique JWT ID (jti)
    import uuid
    jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": "refresh",
        "jti": jti
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Save refresh token to database for rotation tracking
    refresh_token_record = RefreshToken(
        user_id=data["sub"],
        token_jti=jti,
        expires_at=expire,
        is_used=False,
        is_revoked=False
    )
    db.add(refresh_token_record)
    db.commit()
    
    return encoded_jwt, jti


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def blacklist_token(token: str, ttl_seconds: int) -> None:
    """Add token to blacklist in Redis.
    
    Args:
        token: The JWT token to blacklist
        ttl_seconds: Time to live in seconds (should match token expiry)
    """
    # Use token as key, store timestamp when blacklisted
    redis_client.setex(
        f"blacklist:{token}",
        ttl_seconds,
        datetime.utcnow().isoformat()
    )


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted.
    
    Args:
        token: The JWT token to check
        
    Returns:
        True if token is blacklisted, False otherwise
    """
    return redis_client.exists(f"blacklist:{token}") > 0


def blacklist_all_user_tokens(user_id: str, ttl_seconds: int = 86400) -> None:
    """Blacklist all tokens for a user (logout all sessions).
    
    Args:
        user_id: The user ID
        ttl_seconds: Time to live in seconds (default 24 hours)
    """
    # Store user ID in a set with TTL
    # Any token validation will check this
    redis_client.setex(
        f"user_blacklist:{user_id}",
        ttl_seconds,
        datetime.utcnow().isoformat()
    )


def is_user_blacklisted(user_id: str) -> bool:
    """Check if all user tokens are blacklisted.
    
    Args:
        user_id: The user ID to check
        
    Returns:
        True if user is blacklisted, False otherwise
    """
    return redis_client.exists(f"user_blacklist:{user_id}") > 0


# Rate Limiting Functions
def check_rate_limit(ip_address: str, max_attempts: int = 5, window_seconds: int = 900) -> tuple[bool, int]:
    """Check if IP address has exceeded rate limit for login attempts.
    
    Args:
        ip_address: The IP address to check
        max_attempts: Maximum number of attempts allowed (default: 5)
        window_seconds: Time window in seconds (default: 900 = 15 minutes)
        
    Returns:
        Tuple of (is_allowed, attempts_remaining)
    """
    key = f"rate_limit:login:{ip_address}"
    
    # Get current attempt count
    current_attempts = redis_client.get(key)
    
    if current_attempts is None:
        # First attempt
        return (True, max_attempts - 1)
    
    current_attempts = int(current_attempts)
    
    if current_attempts >= max_attempts:
        # Rate limit exceeded
        ttl = redis_client.ttl(key)
        return (False, 0)
    
    # Still within limit
    return (True, max_attempts - current_attempts - 1)


def record_failed_login(ip_address: str, window_seconds: int = 900) -> int:
    """Record a failed login attempt for an IP address.
    
    Args:
        ip_address: The IP address
        window_seconds: Time window in seconds (default: 900 = 15 minutes)
        
    Returns:
        Current number of failed attempts
    """
    key = f"rate_limit:login:{ip_address}"
    
    # Increment counter
    current = redis_client.incr(key)
    
    # Set expiry on first attempt
    if current == 1:
        redis_client.expire(key, window_seconds)
    
    return current


def reset_rate_limit(ip_address: str) -> None:
    """Reset rate limit for an IP address (after successful login).
    
    Args:
        ip_address: The IP address
    """
    key = f"rate_limit:login:{ip_address}"
    redis_client.delete(key)


def get_rate_limit_ttl(ip_address: str) -> int:
    """Get remaining TTL for rate limit.
    
    Args:
        ip_address: The IP address
        
    Returns:
        Remaining seconds until rate limit resets, or -1 if not rate limited
    """
    key = f"rate_limit:login:{ip_address}"
    return redis_client.ttl(key)


# Session Management Constants
SESSION_INACTIVITY_TIMEOUT = 1800  # 30 minutes in seconds
MAX_CONCURRENT_SESSIONS = 5  # Maximum active sessions per user

# Session Management Functions
def get_user_sessions(user_id: str) -> list[dict]:
    """Get all active sessions for a user.
    
    Uses a Redis Set to track sessions per user for better performance.
    
    Args:
        user_id: The user ID
        
    Returns:
        List of session dictionaries with token and metadata
    """
    # Use a Redis Set to track session tokens for this user
    user_sessions_key = f"user_sessions:{user_id}"
    
    # Get all session tokens for this user from the set
    session_tokens = redis_client.smembers(user_sessions_key)
    
    sessions = []
    for token in session_tokens:
        # Ensure token is a string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # Get session data
        session_key = f"session:{token}"
        session_data_str = redis_client.get(session_key)
        
        if session_data_str:
            session_data = json.loads(session_data_str)
            sessions.append({
                "token": token,
                "data": session_data,
                "key": session_key
            })
        else:
            # Session expired or deleted, remove from set
            redis_client.srem(user_sessions_key, token)
    
    # Sort by created_at (oldest first)
    sessions.sort(key=lambda x: x["data"].get("created_at", ""))
    
    return sessions


def create_session(access_token: str, user_id: str, ttl_seconds: int = 86400) -> None:
    """Create a session in Redis with 24-hour TTL.
    
    Enforces maximum concurrent sessions limit. If user already has
    MAX_CONCURRENT_SESSIONS sessions, the oldest session is deleted.
    
    Args:
        access_token: The access token to use as session key
        user_id: The user ID
        ttl_seconds: Time to live in seconds (default: 86400 = 24 hours)
    """
    user_sessions_key = f"user_sessions:{user_id}"
    
    # Check existing session count for this user
    user_sessions = get_user_sessions(user_id)
    
    print(f"DEBUG: Creating session for user {user_id}, current sessions: {len(user_sessions)}, max: {MAX_CONCURRENT_SESSIONS}")
    print(f"DEBUG: Current session tokens: {[s['token'][:10] + '...' for s in user_sessions]}")
    
    logger.debug(
        "Creating session - checking concurrent limit",
        user_id=user_id,
        current_sessions=len(user_sessions),
        max_sessions=MAX_CONCURRENT_SESSIONS
    )
    
    # If at limit, delete oldest session
    if len(user_sessions) >= MAX_CONCURRENT_SESSIONS:
        oldest_session = user_sessions[0]
        oldest_token = oldest_session["token"]
        
        print(f"DEBUG: At limit! Deleting oldest session: {oldest_session['key']}")
        
        # Delete session data
        redis_client.delete(oldest_session["key"])
        
        # Remove from user sessions set
        redis_client.srem(user_sessions_key, oldest_token)
        
        logger.info(
            "Oldest session deleted due to concurrent session limit",
            user_id=user_id,
            sessions_count=len(user_sessions),
            max_sessions=MAX_CONCURRENT_SESSIONS,
            deleted_token_prefix=oldest_token[:10]
        )
    
    # Create new session
    key = f"session:{access_token}"
    now = datetime.utcnow()
    session_data = {
        "user_id": user_id,
        "created_at": now.isoformat(),
        "last_activity": now.isoformat()
    }
    
    # Store session data FIRST before adding to set
    redis_client.setex(key, ttl_seconds, json.dumps(session_data))
    
    # Then add token to user sessions set
    redis_client.sadd(user_sessions_key, access_token)
    
    # Remove any TTL on the set (in case old code set one)
    redis_client.persist(user_sessions_key)
    # The set will be cleaned up when sessions expire via get_user_sessions()
    
    print(f"DEBUG: Session created: {key[:30]}...")


def validate_session(access_token: str) -> bool:
    """Validate that a session exists in Redis.
    
    Args:
        access_token: The access token to check
        
    Returns:
        True if session exists, False otherwise
    """
    key = f"session:{access_token}"
    return redis_client.exists(key) > 0


def get_session(access_token: str) -> dict | None:
    """Get session data from Redis.
    
    Args:
        access_token: The access token
        
    Returns:
        Session data dict or None if not found
    """
    key = f"session:{access_token}"
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None


def delete_session(access_token: str) -> None:
    """Delete a session from Redis and remove from user sessions set.
    
    Args:
        access_token: The access token
    """
    key = f"session:{access_token}"
    
    # Get session data to find user_id
    session_data = get_session(access_token)
    
    # Delete session data
    redis_client.delete(key)
    
    # Remove from user sessions set if we have user_id
    if session_data:
        user_id = session_data.get("user_id")
        if user_id:
            user_sessions_key = f"user_sessions:{user_id}"
            redis_client.srem(user_sessions_key, access_token)


def delete_all_user_sessions(user_id: str) -> int:
    """Delete all sessions for a user.
    
    Uses the user sessions set for efficient deletion.
    
    Args:
        user_id: The user ID
        
    Returns:
        Number of sessions deleted
    """
    user_sessions_key = f"user_sessions:{user_id}"
    
    # Get all session tokens for this user
    session_tokens = redis_client.smembers(user_sessions_key)
    
    deleted = 0
    for token in session_tokens:
        # Ensure token is a string
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        # Delete session
        session_key = f"session:{token}"
        if redis_client.delete(session_key) > 0:
            deleted += 1
    
    # Delete the user sessions set
    redis_client.delete(user_sessions_key)
    
    return deleted


def get_session_ttl(access_token: str) -> int:
    """Get remaining TTL for a session.
    
    Args:
        access_token: The access token
        
    Returns:
        Remaining seconds until session expires, or -1 if not found
    """
    key = f"session:{access_token}"
    return redis_client.ttl(key)


def update_session_activity(access_token: str) -> bool:
    """Update the last_activity timestamp for a session.
    
    Args:
        access_token: The access token
        
    Returns:
        True if session was updated, False if session doesn't exist
    """
    key = f"session:{access_token}"
    session_data = get_session(access_token)
    
    if not session_data:
        return False
    
    # Update last_activity timestamp
    session_data["last_activity"] = datetime.utcnow().isoformat()
    
    # Get current TTL to preserve it
    ttl = redis_client.ttl(key)
    if ttl > 0:
        # Update session data while preserving TTL
        redis_client.setex(key, ttl, json.dumps(session_data))
        return True
    
    return False


def check_session_inactivity(access_token: str, timeout_seconds: int = SESSION_INACTIVITY_TIMEOUT) -> tuple[bool, int]:
    """Check if a session has exceeded the inactivity timeout.
    
    Args:
        access_token: The access token
        timeout_seconds: Inactivity timeout in seconds (default: 1800 = 30 minutes)
        
    Returns:
        Tuple of (is_expired, seconds_since_last_activity)
        is_expired: True if session exceeded timeout, False otherwise
        seconds_since_last_activity: Seconds since last activity, or -1 if session not found
    """
    session_data = get_session(access_token)
    
    if not session_data:
        return (True, -1)
    
    last_activity_str = session_data.get("last_activity")
    if not last_activity_str:
        # Legacy session without last_activity, treat as inactive
        return (True, -1)
    
    try:
        last_activity = datetime.fromisoformat(last_activity_str)
        now = datetime.utcnow()
        
        # Calculate seconds since last activity
        seconds_inactive = int((now - last_activity).total_seconds())
        
        # Check if exceeded timeout
        is_expired = seconds_inactive > timeout_seconds
        
        return (is_expired, seconds_inactive)
    except (ValueError, AttributeError):
        # Invalid timestamp format
        return (True, -1)


# Audit Logging Functions
def create_audit_log(
    db: Session,
    action: str,
    user_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    ip_address: str = None,
    user_agent: str = None,
    extra_data: dict = None
) -> AuditLog:
    """Create an audit log entry.
    
    Args:
        db: Database session
        action: Action performed (e.g., 'login', 'logout', 'register')
        user_id: User ID (optional for actions like failed login)
        resource_type: Type of resource affected (optional)
        resource_id: ID of resource affected (optional)
        ip_address: IP address of request
        user_agent: User agent string
        extra_data: Additional metadata (optional)
        
    Returns:
        Created AuditLog instance
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=extra_data
    )
    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)
    return audit_log


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User agent string
    """
    return request.headers.get("User-Agent", "unknown")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate session exists in Redis
        if not validate_session(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check for inactivity timeout (30 minutes)
        is_expired, seconds_inactive = check_session_inactivity(token, SESSION_INACTIVITY_TIMEOUT)
        if is_expired:
            # Delete expired session
            delete_session(token)
            
            # Log the inactivity timeout
            logger.info(
                "Session expired due to inactivity",
                token_prefix=token[:10],
                seconds_inactive=seconds_inactive
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired due to inactivity",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
        
        # Check if all user tokens are blacklisted (logout all)
        if is_user_blacklisted(user_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="All user sessions have been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last activity timestamp for this session
        update_session_activity(token)
            
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current authenticated user and verify they have admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# API endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/test/slow")
async def test_slow(delay: int = 35):
    """Test endpoint that simulates slow response for timeout testing."""
    logger.info(f"Slow endpoint called with delay={delay}s")
    await asyncio.sleep(delay)
    return {
        "message": f"Response after {delay} seconds",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/test/performance")
async def test_performance(delay: float = 0.5):
    """Test endpoint to simulate requests of varying duration for performance testing."""
    correlation_id = f"perf-test-{int(time.time() * 1000)}"
    
    logger.info(
        "Performance test endpoint called",
        correlation_id=correlation_id,
        requested_delay=delay
    )
    
    # Simulate some processing
    await asyncio.sleep(delay)
    
    return {
        "message": f"Response after {delay} seconds",
        "delay_seconds": delay,
        "timestamp": datetime.utcnow().isoformat(),
        "correlation_id": correlation_id
    }


# In-memory counter for idempotency testing
idempotency_test_counter = {"count": 0}


@app.post("/test/create")
async def test_create(request: Request):
    """Test endpoint for idempotency testing - creates a resource with unique ID."""
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    
    # Increment counter to track actual executions
    idempotency_test_counter["count"] += 1
    execution_count = idempotency_test_counter["count"]
    
    # Simulate resource creation
    resource_id = f"resource_{execution_count}_{datetime.utcnow().timestamp()}"
    
    logger.info(
        "Test resource created",
        correlation_id=correlation_id,
        resource_id=resource_id,
        execution_count=execution_count
    )
    
    return {
        "resource_id": resource_id,
        "execution_count": execution_count,
        "created_at": datetime.utcnow().isoformat(),
        "message": "Resource created successfully"
    }


@app.get("/test/counter")
async def test_counter():
    """Get the current idempotency test counter value."""
    return {
        "count": idempotency_test_counter["count"],
        "message": "Total number of executions of /test/create endpoint"
    }


@app.post("/test/counter/reset")
async def test_counter_reset():
    """Reset the idempotency test counter."""
    idempotency_test_counter["count"] = 0
    return {
        "count": 0,
        "message": "Counter reset successfully"
    }


@app.get("/test/logging")
async def test_logging():
    """Test endpoint to verify different log levels."""
    correlation_id = "test-logging-" + str(int(time.time()))
    
    # Test all log levels
    logger.debug("This is a DEBUG message", correlation_id=correlation_id)
    logger.info("This is an INFO message", correlation_id=correlation_id)
    logger.warning("This is a WARNING message", correlation_id=correlation_id)
    logger.error("This is an ERROR message", correlation_id=correlation_id)
    
    return {
        "message": "Logged messages at all levels",
        "levels": ["DEBUG", "INFO", "WARNING", "ERROR"],
        "correlation_id": correlation_id,
        "current_log_level": os.getenv("LOG_LEVEL", "INFO")
    }


@app.get("/test/error")
async def test_error(user_id: str = "test-user-123", file_id: str = "test-file-456"):
    """Test endpoint to trigger errors with context for error tracking verification."""
    correlation_id = "test-error-" + str(int(time.time()))
    
    try:
        # Simulate an operation that fails
        logger.info(
            "Starting test operation",
            correlation_id=correlation_id,
            user_id=user_id,
            file_id=file_id
        )
        
        # Trigger a division by zero error with context
        result = 1 / 0  # This will raise ZeroDivisionError
        
        return {"result": result}
    except ZeroDivisionError as e:
        # Log the error with full stack trace and context
        logger.exception(
            "Test error triggered successfully",
            exc=e,
            correlation_id=correlation_id,
            user_id=user_id,
            file_id=file_id,
            operation="test_division",
            request_path="/test/error"
        )
        
        # Also test the error method with exception
        logger.error(
            "Alternative error logging method",
            correlation_id=correlation_id,
            exc=e,
            user_id=user_id,
            file_id=file_id
        )
        
        return {
            "message": "Error logged successfully with stack trace",
            "correlation_id": correlation_id,
            "user_id": user_id,
            "file_id": file_id,
            "error_type": type(e).__name__,
            "error_message": str(e)
        }


@app.get("/test/nested-error")
async def test_nested_error():
    """Test endpoint to trigger nested errors with full stack trace."""
    correlation_id = "test-nested-error-" + str(int(time.time()))
    
    def level_3():
        """Innermost function that raises error."""
        return {"data": [1, 2, 3][10]}  # IndexError
    
    def level_2():
        """Middle function."""
        return level_3()
    
    def level_1():
        """Outer function."""
        return level_2()
    
    try:
        result = level_1()
        return result
    except IndexError as e:
        # Log error with nested stack trace
        logger.exception(
            "Nested error captured",
            exc=e,
            correlation_id=correlation_id,
            depth=3,
            function_chain="level_1 -> level_2 -> level_3"
        )
        
        return {
            "message": "Nested error logged with full stack trace",
            "correlation_id": correlation_id,
            "error_type": type(e).__name__,
            "stack_depth": 3
        }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Generate Prometheus format metrics
    metrics_output = generate_latest(registry)
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        print(f"DEBUG: Registration request for email: {user_data.email}")
        
        # Check if user already exists
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
            # Log failed registration
            create_audit_log(
                db=db,
                action="registration_failed",
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"email": user_data.email, "reason": "email_already_exists"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        print(f"DEBUG: Creating new user...")
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False,  # Email not verified yet
            role="user"
        )
        
        print(f"DEBUG: Adding user to database...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"DEBUG: User created successfully with ID: {new_user.id}")
        
        # Create email verification token (valid for 24 hours)
        verification_token = secrets.token_urlsafe(32)
        verification_token_record = EmailVerificationToken(
            user_id=new_user.id,
            token=verification_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(verification_token_record)
        db.commit()
        
        print(f"DEBUG: Verification token created: {verification_token}")
        
        # TODO: Send verification email
        # For now, we'll just log it
        verification_url = f"http://localhost:3000/verify-email?token={verification_token}"
        print(f"DEBUG: Verification URL: {verification_url}")
        logger.info(
            "User registered - email verification required",
            user_id=new_user.id,
            email=new_user.email,
            verification_url=verification_url
        )
        
        # Log successful registration
        create_audit_log(
            db=db,
            action="registration_success",
            user_id=new_user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": new_user.email, "email_verified": False}
        )
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        # Log registration error
        create_audit_log(
            db=db,
            action="registration_error",
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user_data.email, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login and get JWT tokens."""
    # Get client IP and user agent for rate limiting and audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # First, check if user exists and if account is locked
    # (Account lockout check happens BEFORE IP rate limiting to give locked accounts priority)
    user = get_user_by_email(db, user_data.email)
    if user and user.locked_until and datetime.now(timezone.utc) < user.locked_until:
        # Account is locked - show this error instead of rate limit
        time_remaining = (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={
                "email": user_data.email,
                "reason": "account_locked",
                "locked_until": user.locked_until.isoformat(),
                "minutes_remaining": int(time_remaining)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account locked due to too many failed attempts. Please try again in {int(time_remaining)} minutes."
        )
    
    # Check rate limit (IP-based)
    is_allowed, attempts_remaining = check_rate_limit(client_ip)
    if not is_allowed:
        ttl = get_rate_limit_ttl(client_ip)
        # Log failed attempt due to rate limit
        create_audit_log(
            db=db,
            action="login_rate_limited",
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user_data.email, "reason": "rate_limit_exceeded"}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {ttl} seconds."
        )
    
    # Verify user exists (check again in case it wasn't checked above)
    if not user:
        user = get_user_by_email(db, user_data.email)
    if not user:
        # Record failed login attempt
        record_failed_login(client_ip)
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user_data.email, "reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # If lockout period has passed, reset the lockout
    if user.locked_until and datetime.now(timezone.utc) >= user.locked_until:
        user.locked_until = None
        user.failed_login_attempts = 0
        db.commit()
        logger.info(
            "Account lockout expired, reset",
            user_id=user.id,
            email=user.email
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        
        # Lock account if 10 or more failed attempts
        if user.failed_login_attempts >= 10:
            user.locked_until = datetime.now(timezone.utc) + timedelta(hours=1)
            db.commit()
            
            # Log account locked
            create_audit_log(
                db=db,
                action="account_locked",
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={
                    "email": user_data.email,
                    "reason": "too_many_failed_attempts",
                    "attempts": user.failed_login_attempts,
                    "locked_until": user.locked_until.isoformat()
                }
            )
            
            logger.warning(
                "Account locked due to failed login attempts",
                user_id=user.id,
                email=user.email,
                attempts=user.failed_login_attempts,
                locked_until=user.locked_until.isoformat()
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to too many failed attempts. Please try again in 1 hour."
            )
        else:
            db.commit()
        
        # Record failed login attempt (rate limiting)
        record_failed_login(client_ip)
        
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={
                "email": user_data.email,
                "reason": "incorrect_password",
                "failed_attempts": user.failed_login_attempts,
                "remaining_attempts": 10 - user.failed_login_attempts
            }
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user_data.email, "reason": "account_inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Check if email is verified
    if not user.is_verified:
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user_data.email, "reason": "email_not_verified"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    # Reset rate limit on successful password authentication
    reset_rate_limit(client_ip)
    
    # Reset failed login attempts on successful authentication
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        logger.info(
            "Reset failed login attempts after successful login",
            user_id=user.id,
            email=user.email
        )
    
    # Check if MFA is enabled for this user
    if user.mfa_enabled and user.mfa_secret:
        # MFA is enabled - don't create tokens yet
        # User must verify MFA code via /mfa/verify endpoint
        logger.info(
            "Login requires MFA verification",
            user_id=user.id,
            email=user.email
        )
        
        # Log login attempt (MFA required)
        create_audit_log(
            db=db,
            action="login_mfa_required",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={
                "email": user.email,
                "remember_me": user_data.remember_me
            }
        )
        
        # Return a special response indicating MFA is required
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "mfa_required": True,
                "email": user.email,
                "message": "MFA verification required. Please provide your authenticator code."
            }
        )
    
    # MFA not enabled - proceed with normal login
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens with user claims
    access_token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role
    })
    
    # Use 30 days for refresh token if remember_me is true, otherwise use default
    refresh_token_expires_days = 30 if user_data.remember_me else None
    refresh_token, jti = create_refresh_token(
        data={"sub": user.id}, 
        db=db, 
        expires_days=refresh_token_expires_days
    )
    
    # Create session in Redis with 24-hour TTL
    create_session(access_token, user.id, ttl_seconds=86400)
    
    # Log successful login
    create_audit_log(
        db=db,
        action="login_success",
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        extra_data={
            "email": user.email,
            "remember_me": user_data.remember_me
        }
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/token", response_model=Token)
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with OAuth2 form (for compatibility)."""
    # Get client IP and user agent for rate limiting and audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check rate limit
    is_allowed, attempts_remaining = check_rate_limit(client_ip)
    if not is_allowed:
        ttl = get_rate_limit_ttl(client_ip)
        # Log failed attempt due to rate limit
        create_audit_log(
            db=db,
            action="login_rate_limited",
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": form_data.username, "reason": "rate_limit_exceeded"}
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {ttl} seconds.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify user exists
    user = get_user_by_email(db, form_data.username)  # username is email
    if not user:
        # Record failed login attempt
        record_failed_login(client_ip)
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": form_data.username, "reason": "user_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        # Record failed login attempt
        record_failed_login(client_ip)
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": form_data.username, "reason": "incorrect_password"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        # Log failed login
        create_audit_log(
            db=db,
            action="login_failed",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": form_data.username, "reason": "account_inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Reset rate limit on successful login
    reset_rate_limit(client_ip)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens with user claims
    access_token = create_access_token(data={
        "sub": user.id,
        "email": user.email,
        "role": user.role
    })
    refresh_token, jti = create_refresh_token(data={"sub": user.id}, db=db)
    
    # Create session in Redis with 24-hour TTL
    create_session(access_token, user.id, ttl_seconds=86400)
    
    # Log successful login
    create_audit_log(
        db=db,
        action="login_success",
        user_id=user.id,
        ip_address=client_ip,
        user_agent=user_agent,
        extra_data={"email": form_data.username}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/refresh", response_model=Token)
async def refresh_tokens(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token.
    
    Implements token rotation - old refresh token is invalidated.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode refresh token
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")
        
        if user_id is None or token_type != "refresh" or jti is None:
            raise credentials_exception
        
        # Check if refresh token exists in database
        token_record = db.query(RefreshToken).filter(
            RefreshToken.token_jti == jti
        ).first()
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found"
            )
        
        # Check if token is already used (token rotation)
        if token_record.is_used:
            # Token reuse detected - reject the request
            # Note: In a production system, you might want to revoke all tokens
            # for this user as a security measure, but for now we just reject
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token already used"
            )
        
        # Check if token is revoked
        if token_record.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked"
            )
        
        # Check if token is expired
        if token_record.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        
        # Get user
        user = get_user_by_id(db, user_id)
        if not user:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Mark old refresh token as used
        token_record.is_used = True
        token_record.used_at = datetime.now(timezone.utc)
        db.commit()
        
        # Create new tokens
        new_access_token = create_access_token(data={
            "sub": user.id,
            "email": user.email,
            "role": user.role
        })
        new_refresh_token, new_jti = create_refresh_token(data={"sub": user.id}, db=db)
        
        # Create session in Redis with 24-hour TTL
        create_session(new_access_token, user.id, ttl_seconds=86400)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise credentials_exception


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@app.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout current session by blacklisting the access token.
    
    The token will be added to Redis blacklist with TTL matching token expiry.
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Decode token to get expiry
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        
        if exp:
            # Calculate remaining TTL
            now = datetime.utcnow().timestamp()
            ttl = int(exp - now)
            
            if ttl > 0:
                # Blacklist token for remaining TTL
                blacklist_token(token, ttl)
                
                # Delete session from Redis
                delete_session(token)
                
                logger.info(
                    "User logged out",
                    user_id=current_user.id,
                    email=current_user.email,
                    ttl=ttl
                )
                
                # Log logout
                create_audit_log(
                    db=db,
                    action="logout",
                    user_id=current_user.id,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    extra_data={"email": current_user.email}
                )
                
                return {
                    "message": "Successfully logged out",
                    "detail": "Access token has been invalidated"
                }
        
        # If token already expired or no exp claim, just return success
        # Log logout anyway
        create_audit_log(
            db=db,
            action="logout",
            user_id=current_user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": current_user.email, "note": "token_already_expired"}
        )
        
        return {
            "message": "Successfully logged out",
            "detail": "Token was already expired"
        }
        
    except JWTError as e:
        logger.error(
            "Error during logout",
            user_id=current_user.id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )


@app.post("/logout-all")
async def logout_all(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout all sessions by blacklisting all user tokens.
    
    This will invalidate all access tokens for the user across all devices/sessions.
    Also marks all refresh tokens as revoked in the database.
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Blacklist all user tokens in Redis (24 hours TTL to cover max token lifetime)
        blacklist_all_user_tokens(current_user.id, ttl_seconds=86400)
        
        # Delete all user sessions from Redis
        deleted_sessions = delete_all_user_sessions(current_user.id)
        
        # Revoke all refresh tokens in database
        db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_used == False,
            RefreshToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": datetime.now(timezone.utc)
        })
        db.commit()
        
        logger.info(
            "User logged out from all sessions",
            user_id=current_user.id,
            email=current_user.email,
            sessions_deleted=deleted_sessions
        )
        
        # Log logout-all
        create_audit_log(
            db=db,
            action="logout_all",
            user_id=current_user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": current_user.email}
        )
        
        return {
            "message": "Successfully logged out from all sessions",
            "detail": "All access tokens and refresh tokens have been invalidated"
        }
        
    except Exception as e:
        logger.error(
            "Error during logout-all",
            user_id=current_user.id,
            error=str(e)
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout from all sessions"
        )


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Request model for confirming password reset."""
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v


class MFASetupResponse(BaseModel):
    """Response model for MFA setup."""
    secret: str
    qr_code: str  # Base64-encoded QR code image
    provisioning_uri: str


class MFAEnableRequest(BaseModel):
    """Request model for enabling MFA."""
    code: str  # 6-digit TOTP code


class MFAVerifyRequest(BaseModel):
    """Request model for verifying MFA during login."""
    email: EmailStr
    code: str  # 6-digit TOTP code


@app.post("/password-reset/request")
async def request_password_reset(
    request_data: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Request a password reset email.
    
    This endpoint will:
    1. Check if user exists (but don't reveal if they don't for security)
    2. Generate a secure reset token
    3. Store token in database with 1-hour expiry
    4. Send reset email (mocked for now)
    
    Always returns success to prevent user enumeration.
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request_data.email).first()
        
        if user:
            # Generate secure random token (32 bytes = 64 hex characters)
            reset_token = secrets.token_urlsafe(32)
            
            # Calculate expiry (1 hour from now)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            # Invalidate any existing unused tokens for this user
            db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.is_used == False
            ).update({
                "is_used": True,
                "used_at": datetime.now(timezone.utc)
            })
            
            # Create new reset token
            password_reset_token = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            db.add(password_reset_token)
            db.commit()
            
            logger.info(
                "Password reset requested",
                user_id=user.id,
                email=user.email,
                expires_at=expires_at.isoformat()
            )
            
            # Log password reset request
            create_audit_log(
                db=db,
                action="password_reset_requested",
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"email": user.email}
            )
            
            # TODO: Send email with reset link
            # For now, we'll log the token (in production, this would be sent via email)
            logger.info(
                "Password reset token generated (would be sent via email)",
                user_id=user.id,
                email=user.email,
                token=reset_token,
                reset_link=f"http://localhost:3000/reset-password?token={reset_token}"
            )
        else:
            # User not found, but don't reveal this for security
            logger.info(
                "Password reset requested for non-existent email",
                email=request_data.email
            )
            # Still log the attempt
            create_audit_log(
                db=db,
                action="password_reset_requested",
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"email": request_data.email, "note": "user_not_found"}
            )
        
        # Always return success to prevent user enumeration
        return {
            "message": "If an account exists with this email, a password reset link has been sent",
            "detail": "Please check your email for reset instructions"
        }
        
    except Exception as e:
        logger.error(
            "Error during password reset request",
            email=request_data.email,
            error=str(e)
        )
        db.rollback()
        # Still return success to prevent information leakage
        return {
            "message": "If an account exists with this email, a password reset link has been sent",
            "detail": "Please check your email for reset instructions"
        }


@app.post("/password-reset/confirm")
async def confirm_password_reset(
    request_data: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset password using a valid reset token.
    
    This endpoint will:
    1. Validate the reset token
    2. Check if token is expired or already used
    3. Update user's password
    4. Mark token as used
    5. Invalidate all user sessions
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Find reset token
        reset_token = db.query(PasswordResetToken).filter(
            PasswordResetToken.token == request_data.token
        ).first()
        
        if not reset_token:
            # Log failed password reset
            create_audit_log(
                db=db,
                action="password_reset_failed",
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"reason": "invalid_token"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if token is already used
        if reset_token.is_used:
            logger.warning(
                "Attempt to use already-used password reset token",
                token_id=reset_token.id,
                user_id=reset_token.user_id
            )
            # Log failed password reset
            create_audit_log(
                db=db,
                action="password_reset_failed",
                user_id=reset_token.user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"reason": "token_already_used"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset token has already been used"
            )
        
        # Check if token is expired
        now = datetime.now(timezone.utc)
        if now > reset_token.expires_at:
            logger.warning(
                "Attempt to use expired password reset token",
                token_id=reset_token.id,
                user_id=reset_token.user_id,
                expired_at=reset_token.expires_at.isoformat()
            )
            # Log failed password reset
            create_audit_log(
                db=db,
                action="password_reset_failed",
                user_id=reset_token.user_id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"reason": "token_expired"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This reset token has expired. Please request a new one."
            )
        
        # Get user
        user = db.query(User).filter(User.id == reset_token.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Hash new password
        hashed_password = pwd_context.hash(request_data.new_password)
        
        # Update user's password
        user.password_hash = hashed_password
        user.updated_at = now
        
        # Mark token as used
        reset_token.is_used = True
        reset_token.used_at = now
        
        # Invalidate all user sessions (logout from all devices)
        blacklist_all_user_tokens(user.id, ttl_seconds=86400)
        
        # Revoke all refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.is_used == False,
            RefreshToken.is_revoked == False
        ).update({
            "is_revoked": True,
            "revoked_at": now
        })
        
        db.commit()
        
        logger.info(
            "Password reset successful",
            user_id=user.id,
            email=user.email,
            token_id=reset_token.id
        )
        
        # Log successful password reset
        create_audit_log(
            db=db,
            action="password_reset_success",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user.email}
        )
        
        return {
            "message": "Password has been reset successfully",
            "detail": "You can now login with your new password. All existing sessions have been logged out."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error during password reset confirmation",
            error=str(e)
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@app.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate MFA secret and QR code for user to scan with authenticator app.
    
    This endpoint generates a new TOTP secret but does NOT enable MFA yet.
    User must verify the code with /mfa/enable to actually enable MFA.
    """
    try:
        # Generate a new TOTP secret
        secret = pyotp.random_base32()
        
        # Create provisioning URI for QR code
        # Format: otpauth://totp/AutoGraph:user@example.com?secret=SECRET&issuer=AutoGraph
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=current_user.email,
            issuer_name="AutoGraph v3"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Convert QR code to base64-encoded PNG
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Store the secret temporarily (will be saved permanently when user enables MFA)
        # For now, we'll store it in the user record but not enable MFA yet
        current_user.mfa_secret = secret
        db.commit()
        
        logger.info(
            "MFA setup initiated",
            user_id=current_user.id,
            email=current_user.email
        )
        
        return {
            "secret": secret,
            "qr_code": qr_code_base64,
            "provisioning_uri": provisioning_uri
        }
        
    except Exception as e:
        logger.error(
            "Error during MFA setup",
            user_id=current_user.id,
            error=str(e)
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup MFA"
        )


@app.post("/mfa/enable")
async def enable_mfa(
    request_data: MFAEnableRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable MFA for user after verifying TOTP code.
    
    User must first call /mfa/setup to get the secret and QR code,
    then scan the QR code with their authenticator app,
    then call this endpoint with the 6-digit code from the app.
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Check if user has a secret (from /mfa/setup)
        if not current_user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA not set up. Please call /mfa/setup first."
            )
        
        # Verify the TOTP code
        totp = pyotp.TOTP(current_user.mfa_secret)
        if not totp.verify(request_data.code, valid_window=1):
            # Log failed MFA enable attempt
            create_audit_log(
                db=db,
                action="mfa_enable_failed",
                user_id=current_user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"email": current_user.email, "reason": "invalid_code"}
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA code. Please try again."
            )
        
        # Enable MFA for user
        current_user.mfa_enabled = True
        db.commit()
        
        logger.info(
            "MFA enabled successfully",
            user_id=current_user.id,
            email=current_user.email
        )
        
        # Log successful MFA enable
        create_audit_log(
            db=db,
            action="mfa_enabled",
            user_id=current_user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": current_user.email}
        )
        
        return {
            "message": "MFA enabled successfully",
            "detail": "You will now need to enter a code from your authenticator app when logging in."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error enabling MFA",
            user_id=current_user.id,
            error=str(e)
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable MFA"
        )


@app.post("/mfa/verify")
async def verify_mfa(
    request_data: MFAVerifyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify MFA code during login.
    
    This endpoint is called after successful password authentication
    when the user has MFA enabled. It verifies the TOTP code and
    returns JWT tokens if successful.
    """
    # Get client IP and user agent for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Get user by email
        user = db.query(User).filter(User.email == request_data.email).first()
        if not user:
            # Don't reveal whether user exists
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # Check if MFA is enabled
        if not user.mfa_enabled or not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled for this user"
            )
        
        # Verify the TOTP code
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(request_data.code, valid_window=1):
            # Log failed MFA verification
            create_audit_log(
                db=db,
                action="mfa_verify_failed",
                user_id=user.id,
                ip_address=client_ip,
                user_agent=user_agent,
                extra_data={"email": user.email, "reason": "invalid_code"}
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA code"
            )
        
        # MFA verification successful - create tokens
        access_token = create_access_token(data={
            "sub": user.id,
            "email": user.email,
            "role": user.role
        })
        refresh_token, jti = create_refresh_token(data={"sub": user.id}, db=db)
        
        # Create session in Redis with 24-hour TTL
        create_session(access_token, user.id, ttl_seconds=86400)
        
        # Update last login timestamp
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(
            "MFA verification successful",
            user_id=user.id,
            email=user.email
        )
        
        # Log successful MFA verification
        create_audit_log(
            db=db,
            action="mfa_verify_success",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user.email}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error verifying MFA",
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify MFA"
        )


# Email Verification Endpoints


class EmailVerificationRequest(BaseModel):
    """Request model for email verification."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email."""
    email: EmailStr


@app.post("/email/verify")
async def verify_email(
    verification_data: EmailVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Verify user's email address with verification token."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Find the verification token
        token_record = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == verification_data.token
        ).first()
        
        if not token_record:
            logger.warning(
                "Email verification failed - token not found",
                token=verification_data.token[:10] + "...",
                ip_address=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        # Check if token is already used
        if token_record.is_used:
            logger.warning(
                "Email verification failed - token already used",
                user_id=token_record.user_id,
                ip_address=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has already been used"
            )
        
        # Check if token is expired
        if datetime.now(timezone.utc) > token_record.expires_at:
            logger.warning(
                "Email verification failed - token expired",
                user_id=token_record.user_id,
                expired_at=token_record.expires_at.isoformat(),
                ip_address=client_ip
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link expired. Please request a new verification email."
            )
        
        # Get user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Mark email as verified
        user.is_verified = True
        
        # Mark token as used
        token_record.is_used = True
        token_record.used_at = datetime.now(timezone.utc)
        
        db.commit()
        
        # Log successful verification
        create_audit_log(
            db=db,
            action="email_verified",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user.email}
        )
        
        logger.info(
            "Email verified successfully",
            user_id=user.id,
            email=user.email
        )
        
        return {
            "message": "Email verified successfully. You can now log in.",
            "email": user.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Email verification error",
            error=str(e),
            exc=e
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@app.post("/email/resend-verification")
async def resend_verification_email(
    resend_data: ResendVerificationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Resend verification email to user."""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    try:
        # Get user
        user = db.query(User).filter(User.email == resend_data.email).first()
        if not user:
            # Don't reveal if email exists or not
            return {
                "message": "If this email is registered, a verification email has been sent."
            }
        
        # Check if already verified
        if user.is_verified:
            return {
                "message": "Email is already verified. You can log in now."
            }
        
        # Invalidate old tokens for this user
        old_tokens = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False
        ).all()
        
        for old_token in old_tokens:
            old_token.is_used = True
            old_token.used_at = datetime.now(timezone.utc)
        
        # Create new verification token
        verification_token = secrets.token_urlsafe(32)
        verification_token_record = EmailVerificationToken(
            user_id=user.id,
            token=verification_token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        db.add(verification_token_record)
        db.commit()
        
        # TODO: Send verification email
        # For now, we'll just log it
        verification_url = f"http://localhost:3000/verify-email?token={verification_token}"
        logger.info(
            "Verification email resent",
            user_id=user.id,
            email=user.email,
            verification_url=verification_url
        )
        
        # Log resend action
        create_audit_log(
            db=db,
            action="verification_email_resent",
            user_id=user.id,
            ip_address=client_ip,
            user_agent=user_agent,
            extra_data={"email": user.email}
        )
        
        return {
            "message": "Verification email has been sent. Please check your inbox."
        }
        
    except Exception as e:
        logger.error(
            "Resend verification email error",
            error=str(e),
            exc=e
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend verification email: {str(e)}"
        )


@app.post("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify JWT token validity."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "valid": True,
            "user_id": user_id,
            "expires_at": datetime.fromtimestamp(payload.get("exp")).isoformat()
        }
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


@app.get("/test/slow-query")
async def test_slow_query(delay_ms: int = 200, db: Session = Depends(get_db)):
    """Test endpoint to trigger slow database queries for performance monitoring."""
    correlation_id = "test-slow-query-" + str(int(time.time()))
    
    try:
        logger.info(
            "Testing slow query performance monitoring",
            correlation_id=correlation_id,
            delay_ms=delay_ms
        )
        
        # Execute a slow query using pg_sleep
        from sqlalchemy import text
        query = text(f"SELECT pg_sleep({delay_ms / 1000.0}), 'slow query test' as result")
        result = db.execute(query)
        row = result.fetchone()
        
        return {
            "message": "Slow query executed",
            "correlation_id": correlation_id,
            "delay_ms": delay_ms,
            "result": row[1] if row else None,
            "note": "Check logs for slow query warning if delay_ms > 100"
        }
    except Exception as e:
        logger.exception(
            "Error executing slow query test",
            exc=e,
            correlation_id=correlation_id,
            delay_ms=delay_ms
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@app.get("/test/complex-query")
async def test_complex_query(db: Session = Depends(get_db)):
    """Test endpoint to trigger complex query that might be slow without indexes."""
    correlation_id = "test-complex-query-" + str(int(time.time()))
    
    try:
        logger.info(
            "Testing complex query performance",
            correlation_id=correlation_id
        )
        
        # Execute a complex query with JOIN and WHERE
        # This query joins users and files tables
        from sqlalchemy import text
        query = text("""
            SELECT u.id, u.email, u.full_name, u.created_at,
                   COUNT(*) as file_count
            FROM users u
            LEFT JOIN files f ON f.created_by = u.id
            WHERE u.created_at > NOW() - INTERVAL '30 days'
            GROUP BY u.id, u.email, u.full_name, u.created_at
            ORDER BY file_count DESC
            LIMIT 10
        """)
        result = db.execute(query)
        rows = result.fetchall()
        
        return {
            "message": "Complex query executed",
            "correlation_id": correlation_id,
            "user_count": len(rows),
            "note": "Check logs for query duration and EXPLAIN plan if slow"
        }
    except Exception as e:
        logger.exception(
            "Error executing complex query test",
            exc=e,
            correlation_id=correlation_id
        )
        # Don't fail if tables don't exist yet
        return {
            "message": "Complex query test failed (tables may not exist yet)",
            "correlation_id": correlation_id,
            "error": str(e)
        }


@app.get("/test/fast-query")
async def test_fast_query(db: Session = Depends(get_db)):
    """Test endpoint to execute fast query (should not trigger slow query logging)."""
    correlation_id = "test-fast-query-" + str(int(time.time()))
    
    try:
        logger.info(
            "Testing fast query (no slow query warning expected)",
            correlation_id=correlation_id
        )
        
        # Execute a fast query
        from sqlalchemy import text
        query = text("SELECT 1 as result")
        result = db.execute(query)
        row = result.fetchone()
        
        return {
            "message": "Fast query executed",
            "correlation_id": correlation_id,
            "result": row[0] if row else None,
            "note": "This query should NOT trigger slow query warning"
        }
    except Exception as e:
        logger.exception(
            "Error executing fast query test",
            exc=e,
            correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


# Admin endpoints
@app.post("/admin/users/{user_id}/unlock")
async def admin_unlock_user(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    request: Request = None
):
    """
    Admin endpoint to manually unlock a user account.
    
    Feature #102: Account lockout can be manually unlocked by admin
    
    Only users with admin role can access this endpoint.
    """
    correlation_id = f"admin-unlock-{int(time.time() * 1000)}"
    
    logger.info(
        "Admin unlock request received",
        correlation_id=correlation_id,
        admin_id=current_admin.id,
        admin_email=current_admin.email,
        target_user_id=user_id
    )
    
    try:
        # Find the user to unlock
        target_user = get_user_by_id(db, user_id)
        
        if not target_user:
            logger.warning(
                "Admin unlock failed - user not found",
                correlation_id=correlation_id,
                target_user_id=user_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if user is actually locked
        was_locked = False
        if target_user.locked_until and target_user.locked_until > datetime.now(timezone.utc):
            was_locked = True
            logger.info(
                "User is locked, proceeding with unlock",
                correlation_id=correlation_id,
                target_user_id=user_id,
                locked_until=target_user.locked_until.isoformat()
            )
        else:
            logger.info(
                "User is not locked, but resetting failed attempts anyway",
                correlation_id=correlation_id,
                target_user_id=user_id,
                failed_attempts=target_user.failed_login_attempts
            )
        
        # Unlock the account by:
        # 1. Setting locked_until to None
        # 2. Resetting failed_login_attempts to 0
        target_user.locked_until = None
        target_user.failed_login_attempts = 0
        db.commit()
        
        logger.info(
            "Account unlocked successfully by admin",
            correlation_id=correlation_id,
            admin_id=current_admin.id,
            target_user_id=user_id,
            target_user_email=target_user.email,
            was_locked=was_locked
        )
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=current_admin.id,
            action="admin_unlock_user",
            resource_type="user",
            resource_id=user_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "target_user_email": target_user.email,
                "was_locked": was_locked,
                "unlocked_by_admin": current_admin.email
            }
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "message": "Account unlocked successfully",
            "user_id": user_id,
            "email": target_user.email,
            "was_locked": was_locked,
            "unlocked_by": current_admin.email,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error unlocking user account",
            correlation_id=correlation_id,
            exc=e,
            admin_id=current_admin.id,
            target_user_id=user_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlock user account"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AUTH_SERVICE_PORT", "8085")))

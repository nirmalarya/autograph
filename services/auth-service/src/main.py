"""Auth Service - User authentication and authorization."""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
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
from .models import User

load_dotenv()

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


# Pydantic models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


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
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


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
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        print(f"DEBUG: Registration request for email: {user_data.email}")
        
        # Check if user already exists
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user:
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
            role="user"
        )
        
        print(f"DEBUG: Adding user to database...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"DEBUG: User created successfully with ID: {new_user.id}")
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR in register: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login and get JWT tokens."""
    # Verify user exists
    user = get_user_by_email(db, user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.post("/token", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with OAuth2 form (for compatibility)."""
    # Verify user exists
    user = get_user_by_email(db, form_data.username)  # username is email
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("AUTH_SERVICE_PORT", "8085")))

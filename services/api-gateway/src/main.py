"""API Gateway - Routes requests to microservices."""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import os
import sys
import redis
from dotenv import load_dotenv
from datetime import datetime
from jose import JWTError, jwt
import uuid
import logging
import json
import signal
import asyncio
from contextlib import asynccontextmanager
import time

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.python.redis_pool import get_redis_client
from shared.python.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState

# Configure structured logging
class StructuredLogger:
    """Structured logger with JSON output for distributed tracing."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)
        
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
        self.logger.info(json.dumps(log_data))
    
    def info(self, message: str, correlation_id: str = None, **kwargs):
        self.log("info", message, correlation_id, **kwargs)
    
    def error(self, message: str, correlation_id: str = None, **kwargs):
        self.log("error", message, correlation_id, **kwargs)
    
    def warning(self, message: str, correlation_id: str = None, **kwargs):
        self.log("warning", message, correlation_id, **kwargs)

logger = StructuredLogger("api-gateway")

# Prometheus metrics registry
registry = CollectorRegistry()

# Request metrics
request_count = Counter(
    'api_gateway_requests_total',
    'Total number of requests',
    ['method', 'path', 'status_code'],
    registry=registry
)

request_duration = Histogram(
    'api_gateway_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'path'],
    registry=registry
)

active_connections = Gauge(
    'api_gateway_active_connections',
    'Number of active connections',
    registry=registry
)

# Circuit breaker metrics
circuit_breaker_state = Gauge(
    'api_gateway_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['service'],
    registry=registry
)

circuit_breaker_failures = Counter(
    'api_gateway_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service'],
    registry=registry
)

# Redis connection pool metrics
redis_connections = Gauge(
    'api_gateway_redis_connections',
    'Number of Redis connections',
    registry=registry
)

# Rate limit metrics
rate_limit_exceeded = Counter(
    'api_gateway_rate_limit_exceeded_total',
    'Total rate limit exceeded events',
    ['key_type'],
    registry=registry
)

# Redis connection with connection pooling
# Using connection pool with max_connections=50 for high concurrency
# Note: Client is created lazily on first use
def get_redis():
    """Get Redis client with connection pooling."""
    return get_redis_client(db=1)  # Use db 1 for rate limiting

# Custom key function for user-based rate limiting
def get_user_identifier(request: Request) -> str:
    """Get user ID from JWT token or fall back to IP address."""
    # Try to get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    # Fall back to IP address for non-authenticated requests
    return f"ip:{get_remote_address(request)}"

# Rate limiter configuration
limiter = Limiter(
    key_func=get_user_identifier,
    storage_uri=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/1"
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
    logger.info("API Gateway starting up")
    
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
    
    logger.info("API Gateway started successfully")
    
    yield
    
    # Shutdown - wait for in-flight requests to complete
    logger.info(
        "API Gateway shutting down",
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
    
    logger.info("API Gateway shutdown complete")

app = FastAPI(
    title="AutoGraph v3 API Gateway",
    description="API Gateway for AutoGraph v3 microservices",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Timeout configuration (in seconds)
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    "/health",
    "/health/services",
    "/health/circuit-breakers",
    "/metrics",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/token",
    "/api/auth/health",
    "/api/auth/test/",  # All test endpoints
]

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Circuit breakers for each microservice
# Protects against cascading failures by failing fast when a service is down
circuit_breakers = {
    "auth": CircuitBreaker(
        name="auth-service",
        failure_threshold=5,    # Open after 5 failures
        timeout=30.0,           # Wait 30s before trying again
        success_threshold=2,    # Need 2 successes to close
        expected_exception=Exception
    ),
    "diagram": CircuitBreaker(
        name="diagram-service",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
    "ai": CircuitBreaker(
        name="ai-service",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
    "collaboration": CircuitBreaker(
        name="collaboration-service",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
    "git": CircuitBreaker(
        name="git-service",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
    "export": CircuitBreaker(
        name="export-service",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
    "integration": CircuitBreaker(
        name="integration-hub",
        failure_threshold=5,
        timeout=30.0,
        success_threshold=2,
        expected_exception=Exception
    ),
}

# Service endpoints
# In Docker: use service hostnames. Locally: use localhost
# SERVICE_HOST env var allows override (e.g., "localhost" for local dev, service name for docker)
SERVICE_HOST_AUTH = os.getenv("AUTH_SERVICE_HOST", "auth-service")
SERVICE_HOST_DIAGRAM = os.getenv("DIAGRAM_SERVICE_HOST", "diagram-service")
SERVICE_HOST_AI = os.getenv("AI_SERVICE_HOST", "ai-service")
SERVICE_HOST_COLLABORATION = os.getenv("COLLABORATION_SERVICE_HOST", "collaboration-service")
SERVICE_HOST_GIT = os.getenv("GIT_SERVICE_HOST", "git-service")
SERVICE_HOST_EXPORT = os.getenv("EXPORT_SERVICE_HOST", "export-service")
SERVICE_HOST_INTEGRATION = os.getenv("INTEGRATION_HUB_HOST", "integration-hub")

SERVICES = {
    "auth": f"http://{SERVICE_HOST_AUTH}:{os.getenv('AUTH_SERVICE_PORT', '8085')}",
    "diagram": f"http://{SERVICE_HOST_DIAGRAM}:{os.getenv('DIAGRAM_SERVICE_PORT', '8082')}",
    "ai": f"http://{SERVICE_HOST_AI}:{os.getenv('AI_SERVICE_PORT', '8084')}",
    "collaboration": f"http://{SERVICE_HOST_COLLABORATION}:{os.getenv('COLLABORATION_SERVICE_PORT', '8083')}",
    "git": f"http://{SERVICE_HOST_GIT}:{os.getenv('GIT_SERVICE_PORT', '8087')}",
    "export": f"http://{SERVICE_HOST_EXPORT}:{os.getenv('EXPORT_SERVICE_PORT', '8097')}",
    "integration": f"http://{SERVICE_HOST_INTEGRATION}:{os.getenv('INTEGRATION_HUB_PORT', '8099')}",
}


def verify_jwt_token(token: str) -> dict:
    """Verify JWT token and return payload."""
    try:
        # Decode and verify token (includes expiration check)
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": True}  # Explicitly verify expiration
        )
        token_type = payload.get("type")
        
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Middleware to enforce request timeout."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    try:
        # Apply timeout to request processing
        response = await asyncio.wait_for(
            call_next(request),
            timeout=REQUEST_TIMEOUT
        )
        return response
    except asyncio.TimeoutError:
        logger.error(
            "Request timeout exceeded",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            timeout=REQUEST_TIMEOUT
        )
        return JSONResponse(
            status_code=504,
            content={
                "detail": f"Request timeout exceeded ({REQUEST_TIMEOUT}s)",
                "timeout": REQUEST_TIMEOUT
            },
            headers={"X-Correlation-ID": correlation_id}
        )


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


@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    """Middleware to authenticate requests using JWT."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Check if route is public
    path = request.url.path
    if any(path.startswith(route) for route in PUBLIC_ROUTES):
        return await call_next(request)
    
    # Get authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning(
            "Authentication failed: missing header",
            correlation_id=correlation_id,
            path=path
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header missing"}
        )
    
    # Extract token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(
            "Authentication failed: invalid header format",
            correlation_id=correlation_id,
            path=path
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid authorization header format"}
        )
    
    token = parts[1]
    
    # Verify token
    try:
        payload = verify_jwt_token(token)
        # Add user_id to request state for downstream services
        request.state.user_id = payload.get("sub")
        
        logger.info(
            "Authentication successful",
            correlation_id=correlation_id,
            user_id=payload.get("sub"),
            path=path
        )
    except HTTPException as e:
        logger.warning(
            "Authentication failed: invalid token",
            correlation_id=correlation_id,
            error=str(e.detail),
            path=path
        )
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    
    return await call_next(request)


@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    """Middleware to handle idempotency keys for duplicate prevention."""
    # Only apply to POST, PUT, PATCH (mutating operations)
    if request.method not in ["POST", "PUT", "PATCH"]:
        return await call_next(request)
    
    # Get idempotency key from header
    idempotency_key = request.headers.get("Idempotency-Key") or request.headers.get("X-Idempotency-Key")
    
    if not idempotency_key:
        # No idempotency key provided, process normally
        return await call_next(request)
    
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = getattr(request.state, "user_id", "anonymous")
    
    # Create Redis key: idempotency:{user_id}:{idempotency_key}:{path}
    # Include path to allow same key for different endpoints
    redis_key = f"idempotency:{user_id}:{idempotency_key}:{request.url.path}"
    
    try:
        redis_client = get_redis()
        
        # Check if we've seen this idempotency key before
        cached_response = redis_client.get(redis_key)
        
        if cached_response:
            # Return cached response
            cached_data = json.loads(cached_response)
            
            logger.info(
                "Idempotency key found - returning cached response",
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                path=request.url.path,
                cached_status=cached_data.get("status_code")
            )
            
            return JSONResponse(
                content=cached_data.get("body"),
                status_code=cached_data.get("status_code", 200),
                headers={
                    **cached_data.get("headers", {}),
                    "X-Idempotency-Hit": "true",
                    "X-Correlation-ID": correlation_id
                }
            )
        
        # Process request normally
        logger.info(
            "Idempotency key not found - processing request",
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            path=request.url.path
        )
        
        response = await call_next(request)
        
        # Cache successful responses (2xx status codes)
        if 200 <= response.status_code < 300:
            # Read response body
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parse JSON body
            try:
                body_json = json.loads(body.decode())
            except:
                body_json = {"data": body.decode()}
            
            # Cache response for 24 hours
            cache_data = {
                "status_code": response.status_code,
                "body": body_json,
                "headers": {
                    k: v for k, v in response.headers.items()
                    if k.lower() not in ["content-length", "transfer-encoding", "content-encoding"]
                }
            }
            
            redis_client.setex(
                redis_key,
                86400,  # 24 hours TTL
                json.dumps(cache_data)
            )
            
            logger.info(
                "Idempotency response cached",
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
                path=request.url.path,
                ttl=86400
            )
            
            # Return new response with body
            return JSONResponse(
                content=body_json,
                status_code=response.status_code,
                headers={
                    **dict(response.headers),
                    "X-Idempotency-Hit": "false"
                }
            )
        
        # Don't cache error responses, just return them
        return response
        
    except Exception as e:
        logger.error(
            "Idempotency middleware error",
            correlation_id=correlation_id,
            error=str(e),
            idempotency_key=idempotency_key
        )
        # On error, process request normally
        return await call_next(request)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware to add correlation ID for distributed tracing."""
    # Get or generate correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Store in request state
    request.state.correlation_id = correlation_id
    
    # Log incoming request
    logger.info(
        "Incoming request",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        client_ip=get_remote_address(request)
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log outgoing response
        logger.info(
            "Outgoing response",
            correlation_id=correlation_id,
            status_code=response.status_code,
            method=request.method,
            path=request.url.path
        )
        
        return response
    except Exception as e:
        # Log error with correlation ID
        logger.error(
            "Request processing error",
            correlation_id=correlation_id,
            error=str(e),
            method=request.method,
            path=request.url.path
        )
        raise


@app.get("/health")
@limiter.limit("1000/minute")  # IP-based rate limit
async def health_check(request: Request):
    """API Gateway health check."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint."""
    # Update circuit breaker state metrics
    for service_name, breaker in circuit_breakers.items():
        # Map state to numeric value: CLOSED=0, OPEN=1, HALF_OPEN=2
        state_value = 0
        if breaker.state.value == "open":
            state_value = 1
        elif breaker.state.value == "half_open":
            state_value = 2
        
        circuit_breaker_state.labels(service=service_name).set(state_value)
    
    # Generate Prometheus format metrics
    metrics_output = generate_latest(registry)
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


@app.get("/health/services")
@limiter.limit("1000/minute")  # IP-based rate limit
async def services_health(request: Request):
    """Check health of all microservices."""
    health_status = {}
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                health_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url,
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                }
            except Exception as e:
                health_status[service_name] = {
                    "status": "unreachable",
                    "url": service_url,
                    "error": str(e)
                }
    
    # Overall status
    all_healthy = all(s["status"] == "healthy" for s in health_status.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": health_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/circuit-breakers")
@limiter.limit("1000/minute")  # IP-based rate limit
async def circuit_breakers_status(request: Request):
    """Get circuit breaker status for all services."""
    breaker_status = {}
    
    for service_name, breaker in circuit_breakers.items():
        breaker_status[service_name] = breaker.get_stats()
    
    return {
        "circuit_breakers": breaker_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("1000/minute")  # IP-based for auth (public routes)
async def proxy_auth(path: str, request: Request):
    """Route requests to auth service."""
    return await proxy_request("auth", path, request)


@app.api_route("/api/diagrams/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_diagrams(path: str, request: Request):
    """Route requests to diagram service."""
    return await proxy_request("diagram", path, request)


@app.api_route("/api/ai/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_ai(path: str, request: Request):
    """Route requests to AI service."""
    return await proxy_request("ai", path, request)


@app.api_route("/api/collaboration/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_collaboration(path: str, request: Request):
    """Route requests to collaboration service."""
    return await proxy_request("collaboration", path, request)


@app.api_route("/api/git/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_git(path: str, request: Request):
    """Route requests to git service."""
    return await proxy_request("git", path, request)


@app.api_route("/api/export/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_export(path: str, request: Request):
    """Route requests to export service."""
    return await proxy_request("export", path, request)


@app.api_route("/api/integrations/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_integrations(path: str, request: Request):
    """Route requests to integration hub."""
    return await proxy_request("integration", path, request)


async def proxy_request(service_name: str, path: str, request: Request):
    """Proxy request to microservice with correlation ID and circuit breaker protection."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    service_url = SERVICES.get(service_name)
    if not service_url:
        logger.error(
            "Service not found",
            correlation_id=correlation_id,
            service=service_name
        )
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
    
    # Get circuit breaker for this service
    circuit_breaker = circuit_breakers.get(service_name)
    if not circuit_breaker:
        logger.warning(
            "No circuit breaker configured for service",
            correlation_id=correlation_id,
            service=service_name
        )
    
    # Build target URL
    target_url = f"{service_url}/{path}"
    
    # Get request body
    body = await request.body()
    
    # Prepare headers with correlation ID
    headers = dict(request.headers)
    headers["X-Correlation-ID"] = correlation_id
    
    # Forward user_id if available
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        headers["X-User-ID"] = str(user_id)
    
    logger.info(
        "Forwarding request to service",
        correlation_id=correlation_id,
        service=service_name,
        target_url=target_url,
        method=request.method,
        circuit_state=circuit_breaker.state.value if circuit_breaker else "none"
    )
    
    # Check circuit breaker before making request
    if circuit_breaker and circuit_breaker.state == CircuitState.OPEN:
        if not circuit_breaker._should_attempt_reset():
            logger.error(
                "Circuit breaker open - failing fast",
                correlation_id=correlation_id,
                service=service_name,
                circuit_state=circuit_breaker.state.value,
                failure_count=circuit_breaker.failure_count
            )
            raise HTTPException(
                status_code=503,
                detail=f"Service {service_name} temporarily unavailable (circuit breaker open)"
            )
        else:
            # Move to half-open to test
            circuit_breaker._state = CircuitState.HALF_OPEN
            circuit_breaker._success_count = 0
            logger.info(f"Circuit breaker '{circuit_breaker.name}' moved to HALF_OPEN state")
    
    # Forward request
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                params=dict(request.query_params),
                content=body
            )
            
            logger.info(
                "Service response received",
                correlation_id=correlation_id,
                service=service_name,
                status_code=response.status_code,
                response_time_ms=response.elapsed.total_seconds() * 1000
            )
            
            # Mark success in circuit breaker
            if circuit_breaker:
                circuit_breaker._on_success()
            
            return JSONResponse(
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        except httpx.ConnectError:
            # Mark failure in circuit breaker
            if circuit_breaker:
                circuit_breaker._on_failure()
            logger.error(
                "Service connection failed",
                correlation_id=correlation_id,
                service=service_name,
                target_url=target_url,
                circuit_state=circuit_breaker.state.value if circuit_breaker else "none",
                failure_count=circuit_breaker.failure_count if circuit_breaker else 0
            )
            raise HTTPException(status_code=503, detail=f"Service {service_name} unavailable")
        except Exception as e:
            # Mark failure in circuit breaker
            if circuit_breaker:
                circuit_breaker._on_failure()
            logger.error(
                "Proxy error",
                correlation_id=correlation_id,
                service=service_name,
                error=str(e),
                error_type=type(e).__name__,
                circuit_state=circuit_breaker.state.value if circuit_breaker else "none"
            )
            raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_GATEWAY_PORT", "8080")))

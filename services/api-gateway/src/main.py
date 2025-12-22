"""API Gateway - Routes requests to microservices."""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

app = FastAPI(
    title="AutoGraph v3 API Gateway",
    description="API Gateway for AutoGraph v3 microservices",
    version="1.0.0"
)

# Add rate limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

# Public routes that don't require authentication
PUBLIC_ROUTES = [
    "/health",
    "/health/services",
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/token",
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
SERVICES = {
    "auth": f"http://localhost:{os.getenv('AUTH_SERVICE_PORT', '8085')}",
    "diagram": f"http://localhost:{os.getenv('DIAGRAM_SERVICE_PORT', '8082')}",
    "ai": f"http://localhost:{os.getenv('AI_SERVICE_PORT', '8084')}",
    "collaboration": f"http://localhost:{os.getenv('COLLABORATION_SERVICE_PORT', '8083')}",
    "git": f"http://localhost:{os.getenv('GIT_SERVICE_PORT', '8087')}",
    "export": f"http://localhost:{os.getenv('EXPORT_SERVICE_PORT', '8097')}",
    "integration": f"http://localhost:{os.getenv('INTEGRATION_HUB_PORT', '8099')}",
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
    async with httpx.AsyncClient(timeout=30.0) as client:
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

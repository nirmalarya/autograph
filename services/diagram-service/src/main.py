"""Diagram Service - Diagram CRUD and storage."""
from fastapi import FastAPI, Request
from datetime import datetime
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

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

logger = StructuredLogger("diagram-service")

app = FastAPI(
    title="AutoGraph v3 Diagram Service",
    description="Diagram CRUD and storage service",
    version="1.0.0"
)

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


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "diagram-service",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def list_diagrams(request: Request):
    """List diagrams endpoint (protected)."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID", "unknown")
    
    logger.info(
        "Listing diagrams",
        correlation_id=correlation_id,
        user_id=user_id
    )
    
    # This endpoint requires authentication from API Gateway
    return {
        "diagrams": [],
        "total": 0,
        "message": "Diagram list endpoint - authentication verified"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DIAGRAM_SERVICE_PORT", "8082")))

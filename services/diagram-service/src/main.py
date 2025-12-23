"""Diagram Service - Diagram CRUD and storage."""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from datetime import datetime
from pydantic import BaseModel, validator
from typing import Optional, Dict, Any
import os
import json
import logging
import signal
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import time
from sqlalchemy.orm import Session

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Import database and models
from .database import get_db
from .models import File, User, Version

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
    
    def warning(self, message: str, correlation_id: str = None, **kwargs):
        self.log("warning", message, correlation_id, **kwargs)

logger = StructuredLogger("diagram-service")

# Prometheus metrics registry
registry = CollectorRegistry()

# Request metrics
request_count = Counter(
    'diagram_service_requests_total',
    'Total number of requests',
    ['method', 'path', 'status_code'],
    registry=registry
)

request_duration = Histogram(
    'diagram_service_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'path'],
    registry=registry
)

active_connections = Gauge(
    'diagram_service_active_connections',
    'Number of active connections',
    registry=registry
)

# Diagram-specific metrics
diagrams_created = Counter(
    'diagram_service_diagrams_created_total',
    'Total diagrams created',
    registry=registry
)

diagrams_updated = Counter(
    'diagram_service_diagrams_updated_total',
    'Total diagrams updated',
    registry=registry
)

diagrams_deleted = Counter(
    'diagram_service_diagrams_deleted_total',
    'Total diagrams deleted',
    registry=registry
)

# Storage metrics
storage_operations = Counter(
    'diagram_service_storage_operations_total',
    'Total storage operations',
    ['operation'],  # upload, download, delete
    registry=registry
)

storage_operation_duration = Histogram(
    'diagram_service_storage_operation_duration_seconds',
    'Storage operation duration in seconds',
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
    logger.info("Diagram Service starting up")
    
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
    
    logger.info("Diagram Service started successfully")
    
    yield
    
    # Shutdown - wait for in-flight requests to complete
    logger.info(
        "Diagram Service shutting down",
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
    
    logger.info("Diagram Service shutdown complete")

app = FastAPI(
    title="AutoGraph v3 Diagram Service",
    description="Diagram CRUD and storage service",
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


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "diagram-service",
        "instance_id": os.getenv("INSTANCE_ID", "default"),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    # Generate Prometheus format metrics
    metrics_output = generate_latest(registry)
    return Response(content=metrics_output, media_type=CONTENT_TYPE_LATEST)


@app.get("/")
async def list_diagrams(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    file_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List diagrams endpoint with pagination, filtering, and search."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing diagrams",
        correlation_id=correlation_id,
        user_id=user_id,
        page=page,
        page_size=page_size,
        file_type=file_type,
        search=search
    )
    
    # Build query
    query = db.query(File).filter(
        File.owner_id == user_id,
        File.is_deleted == False
    )
    
    # Apply filters
    if file_type:
        if file_type not in ['canvas', 'note', 'mixed']:
            raise HTTPException(status_code=400, detail="Invalid file_type. Must be: canvas, note, or mixed")
        query = query.filter(File.file_type == file_type)
    
    # Apply search
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(File.title.ilike(search_pattern))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    diagrams = query.order_by(File.updated_at.desc()).offset(offset).limit(page_size).all()
    
    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size  # Ceiling division
    
    logger.info(
        "Diagrams listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        total=total,
        page=page,
        total_pages=total_pages,
        returned=len(diagrams)
    )
    
    return {
        "diagrams": [DiagramResponse.model_validate(d) for d in diagrams],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


# Pydantic models for request/response with validation
class CreateDiagramRequest(BaseModel):
    """Request model for creating a diagram."""
    title: str
    file_type: str = "canvas"  # canvas, note, mixed
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    folder_id: Optional[str] = None
    
    @validator('title')
    def validate_title(cls, v):
        """Validate diagram title has reasonable length and content."""
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) > 255:
            raise ValueError('Title must not exceed 255 characters')
        # Remove leading/trailing whitespace
        return v.strip()
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type is one of the allowed values."""
        allowed_types = ['canvas', 'note', 'mixed']
        if v not in allowed_types:
            raise ValueError(f'File type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('note_content')
    def validate_note_content(cls, v):
        """Validate note content has reasonable length."""
        if v is not None and len(v) > 1000000:  # 1MB limit
            raise ValueError('Note content must not exceed 1MB')
        return v


class DiagramResponse(BaseModel):
    """Response model for diagram."""
    id: str
    title: str
    file_type: str
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    owner_id: str
    folder_id: Optional[str] = None
    is_starred: bool
    is_deleted: bool
    view_count: int
    current_version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UpdateDiagramRequest(BaseModel):
    """Request model for updating a diagram."""
    title: Optional[str] = None
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    description: Optional[str] = None  # Version description
    expected_version: Optional[int] = None  # For optimistic locking
    
    @validator('title')
    def validate_title(cls, v):
        """Validate diagram title has reasonable length and content."""
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError('Title cannot be empty')
            if len(v) > 255:
                raise ValueError('Title must not exceed 255 characters')
            # Remove leading/trailing whitespace
            return v.strip()
        return v
    
    @validator('note_content')
    def validate_note_content(cls, v):
        """Validate note content has reasonable length."""
        if v is not None and len(v) > 1000000:  # 1MB limit
            raise ValueError('Note content must not exceed 1MB')
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate version description has reasonable length."""
        if v is not None and len(v) > 1000:
            raise ValueError('Description must not exceed 1000 characters')
        return v
    
    @validator('expected_version')
    def validate_expected_version(cls, v):
        """Validate expected version is positive."""
        if v is not None and v < 1:
            raise ValueError('Expected version must be positive')
        return v


class VersionResponse(BaseModel):
    """Response model for version."""
    id: str
    file_id: str
    version_number: int
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


def create_version(db: Session, file: File, description: Optional[str] = None, created_by: Optional[str] = None) -> Version:
    """Create a new version for a file with auto-incremented version number."""
    # Get the highest version number for this file
    max_version = db.query(Version).filter(Version.file_id == file.id).count()
    next_version_number = max_version + 1
    
    # Create new version
    new_version = Version(
        file_id=file.id,
        version_number=next_version_number,
        canvas_data=file.canvas_data,
        note_content=file.note_content,
        description=description,
        created_by=created_by
    )
    
    db.add(new_version)
    
    # Update file's current_version
    file.current_version = next_version_number
    
    return new_version


@app.post("/", response_model=DiagramResponse)
async def create_diagram(
    request: Request,
    diagram: CreateDiagramRequest,
    db: Session = Depends(get_db)
):
    """Create a new diagram."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating diagram",
        correlation_id=correlation_id,
        user_id=user_id,
        title=diagram.title,
        file_type=diagram.file_type
    )
    
    # Create new diagram
    new_diagram = File(
        title=diagram.title,
        owner_id=user_id,
        file_type=diagram.file_type,
        canvas_data=diagram.canvas_data,
        note_content=diagram.note_content,
        folder_id=diagram.folder_id
    )
    
    db.add(new_diagram)
    db.flush()  # Get the diagram ID without committing yet
    
    # Create initial version (version 1)
    create_version(db, new_diagram, description="Initial version", created_by=user_id)
    
    db.commit()
    db.refresh(new_diagram)
    
    # Update metrics
    diagrams_created.inc()
    
    logger.info(
        "Diagram created successfully",
        correlation_id=correlation_id,
        diagram_id=new_diagram.id,
        user_id=user_id,
        version=new_diagram.current_version
    )
    
    return new_diagram


@app.get("/{diagram_id}", response_model=DiagramResponse)
async def get_diagram(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a diagram by ID."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Fetching diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Query diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization - user must own the diagram
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized access attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="You do not have permission to access this diagram")
    
    logger.info(
        "Diagram fetched successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id
    )
    
    return diagram


@app.put("/{diagram_id}", response_model=DiagramResponse)
async def update_diagram(
    diagram_id: str,
    request: Request,
    update_data: UpdateDiagramRequest,
    db: Session = Depends(get_db)
):
    """Update a diagram and create a new version."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Updating diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Query diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization - user must own the diagram
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized update attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="You do not have permission to update this diagram")
    
    # Optimistic locking: Check if expected version matches current version
    if update_data.expected_version is not None:
        if diagram.current_version != update_data.expected_version:
            logger.warning(
                "Version conflict detected",
                correlation_id=correlation_id,
                diagram_id=diagram_id,
                expected_version=update_data.expected_version,
                current_version=diagram.current_version
            )
            raise HTTPException(
                status_code=409, 
                detail=f"Diagram was modified by another user. Expected version {update_data.expected_version}, but current version is {diagram.current_version}. Please refresh and try again."
            )
    
    # Update diagram fields
    if update_data.title is not None:
        diagram.title = update_data.title
    if update_data.canvas_data is not None:
        diagram.canvas_data = update_data.canvas_data
    if update_data.note_content is not None:
        diagram.note_content = update_data.note_content
    
    # Create new version with auto-incremented version number
    create_version(db, diagram, description=update_data.description, created_by=user_id)
    
    db.commit()
    db.refresh(diagram)
    
    # Update metrics
    diagrams_updated.inc()
    
    logger.info(
        "Diagram updated successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id,
        new_version=diagram.current_version
    )
    
    return diagram


@app.get("/{diagram_id}/versions", response_model=list[VersionResponse])
async def get_versions(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all versions for a diagram."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    logger.info(
        "Fetching versions",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Verify diagram exists
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        logger.warning(
            "Diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Query all versions ordered by version_number
    versions = db.query(Version).filter(
        Version.file_id == diagram_id
    ).order_by(Version.version_number).all()
    
    logger.info(
        "Versions fetched successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_count=len(versions)
    )
    
    return versions


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DIAGRAM_SERVICE_PORT", "8082")))

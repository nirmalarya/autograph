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
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import or_, cast, String, func
import httpx

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Import database and models
from .database import get_db
from .models import File, User, Version, Folder, Share, Template

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
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List diagrams endpoint with pagination, filtering, search, and sorting."""
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
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
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
    
    # Apply full-text search with fuzzy matching
    if search:
        # Exact match pattern for traditional search
        search_pattern = f"%{search}%"
        
        # Fuzzy matching using pg_trgm similarity
        # similarity() returns a value between 0 and 1 (higher = more similar)
        # We use 0.25 as threshold (25% similarity) for typo tolerance
        # This allows for 2-3 character typos in typical words
        similarity_threshold = 0.25
        
        # Search in title, note_content, and canvas_data (text elements)
        # Use OR to match any of these fields
        # Combine exact matching (ILIKE) with fuzzy matching (similarity)
        query = query.filter(
            or_(
                # Exact matches (case-insensitive)
                File.title.ilike(search_pattern),
                File.note_content.ilike(search_pattern),
                cast(File.canvas_data, String).ilike(search_pattern),
                # Fuzzy matches using trigram similarity
                func.similarity(File.title, search) >= similarity_threshold,
                func.similarity(File.note_content, search) >= similarity_threshold
            )
        )
        
        # Order fuzzy search results by relevance (similarity score)
        # Higher similarity scores appear first
        query = query.order_by(
            func.greatest(
                func.similarity(File.title, search),
                func.similarity(func.coalesce(File.note_content, ''), search)
            ).desc()
        )
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    # Note: If search is active, results are already ordered by relevance
    # Additional sorting can be applied as secondary sort
    if not search or sort_by:
        # Default: sort by updated_at desc (most recently updated first)
        sort_field = File.updated_at
        sort_direction = 'desc'
        
        if sort_by:
            # Validate sort_by parameter
            valid_sort_fields = {
                'title': File.title,
                'name': File.title,  # Alias for title
                'created_at': File.created_at,
                'created': File.created_at,  # Alias
                'updated_at': File.updated_at,
                'updated': File.updated_at,  # Alias
                'last_viewed': File.last_accessed_at,
                'last_viewed_at': File.last_accessed_at,
                'last_accessed_at': File.last_accessed_at
            }
            
            if sort_by.lower() not in valid_sort_fields:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid sort_by. Must be one of: {', '.join(set(valid_sort_fields.keys()))}"
                )
            
            sort_field = valid_sort_fields[sort_by.lower()]
        
        if sort_order:
            # Validate sort_order parameter
            if sort_order.lower() not in ['asc', 'desc']:
                raise HTTPException(status_code=400, detail="Invalid sort_order. Must be: asc or desc")
            sort_direction = sort_order.lower()
        
        # Apply the sort (as secondary sort if search is active)
        if sort_direction == 'desc':
            query = query.order_by(sort_field.desc())
        else:
            query = query.order_by(sort_field.asc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    diagrams = query.offset(offset).limit(page_size).all()
    
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
    thumbnail_url: Optional[str] = None
    is_starred: bool
    is_deleted: bool
    view_count: int
    current_version: int
    last_edited_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    
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


class CreateTemplateRequest(BaseModel):
    """Request model for creating a template."""
    name: str
    description: Optional[str] = None
    file_type: str = "canvas"
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = []
    is_public: bool = False


class TemplateResponse(BaseModel):
    """Response model for template."""
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    file_type: str
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: bool
    usage_count: int
    category: Optional[str] = None
    tags: Optional[list] = []
    created_at: datetime
    updated_at: datetime
    
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


async def generate_thumbnail(diagram_id: str, canvas_data: dict) -> Optional[str]:
    """
    Generate a thumbnail for a diagram and store it in MinIO.
    
    Returns the MinIO URL of the thumbnail, or None if generation fails.
    """
    try:
        # Call export-service to generate thumbnail
        export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://export-service:8097")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/thumbnail",
                json={
                    "diagram_id": diagram_id,
                    "canvas_data": canvas_data or {},
                    "width": 256,
                    "height": 256
                }
            )
            
            if response.status_code != 200:
                logger.warning(
                    "Thumbnail generation failed",
                    diagram_id=diagram_id,
                    status_code=response.status_code
                )
                return None
            
            thumbnail_data = response.json()
            thumbnail_base64 = thumbnail_data.get("thumbnail_base64")
            
            if not thumbnail_base64:
                logger.warning("No thumbnail data returned", diagram_id=diagram_id)
                return None
            
            # Decode base64 and upload to MinIO
            import base64
            from minio import Minio
            from io import BytesIO
            
            thumbnail_bytes = base64.b64decode(thumbnail_base64)
            
            # Connect to MinIO
            minio_client = Minio(
                os.getenv("MINIO_ENDPOINT", "minio:9000"),
                access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
                secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
                secure=False
            )
            
            # Upload thumbnail to MinIO
            bucket_name = "diagrams"
            object_name = f"thumbnails/{diagram_id}.png"
            
            minio_client.put_object(
                bucket_name,
                object_name,
                BytesIO(thumbnail_bytes),
                len(thumbnail_bytes),
                content_type="image/png"
            )
            
            # Return the MinIO URL
            thumbnail_url = f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}/{bucket_name}/{object_name}"
            
            logger.info(
                "Thumbnail generated and stored",
                diagram_id=diagram_id,
                thumbnail_url=thumbnail_url
            )
            
            return thumbnail_url
            
    except Exception as e:
        logger.error(
            "Error generating thumbnail",
            diagram_id=diagram_id,
            error=str(e)
        )
        return None


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
    
    # Generate thumbnail asynchronously (don't block on failure)
    if diagram.canvas_data:
        try:
            thumbnail_url = await generate_thumbnail(new_diagram.id, diagram.canvas_data)
            if thumbnail_url:
                new_diagram.thumbnail_url = thumbnail_url
        except Exception as e:
            logger.warning(
                "Thumbnail generation failed, continuing without thumbnail",
                correlation_id=correlation_id,
                diagram_id=new_diagram.id,
                error=str(e)
            )
    
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
        version=new_diagram.current_version,
        has_thumbnail=new_diagram.thumbnail_url is not None
    )
    
    return new_diagram


# ============================================================================
# TEMPLATE ENDPOINTS (Must be before /{diagram_id} to avoid route conflicts)
# ============================================================================

@app.post("/templates", response_model=TemplateResponse)
async def create_template(
    request: Request,
    template: CreateTemplateRequest,
    db: Session = Depends(get_db)
):
    """Save a diagram as a template."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating template",
        correlation_id=correlation_id,
        user_id=user_id,
        template_name=template.name
    )
    
    try:
        # Create template
        new_template = Template(
            id=str(uuid.uuid4()),
            name=template.name,
            description=template.description,
            owner_id=user_id,
            file_type=template.file_type,
            canvas_data=template.canvas_data,
            note_content=template.note_content,
            category=template.category,
            tags=template.tags or [],
            is_public=template.is_public,
            usage_count=0
        )
        
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        # Metrics
        diagrams_created.inc()
        request_duration.labels(method="POST", path="/templates").observe(time.time() - start_time)
        request_count.labels(method="POST", path="/templates", status_code=201).inc()
        
        logger.info(
            "Template created successfully",
            correlation_id=correlation_id,
            template_id=new_template.id,
            template_name=new_template.name
        )
        
        return new_template
        
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create template",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to create template: {str(e)}")


@app.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    request: Request,
    db: Session = Depends(get_db),
    category: Optional[str] = None,
    is_public: Optional[bool] = None
):
    """List available templates."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing templates",
        correlation_id=correlation_id,
        user_id=user_id,
        category=category,
        is_public=is_public
    )
    
    try:
        # Build query - show user's templates + public templates
        query = db.query(Template).filter(
            (Template.owner_id == user_id) | (Template.is_public == True)
        )
        
        # Apply filters
        if category:
            query = query.filter(Template.category == category)
        if is_public is not None:
            query = query.filter(Template.is_public == is_public)
        
        # Order by usage count (most popular first) then by created date
        templates = query.order_by(Template.usage_count.desc(), Template.created_at.desc()).all()
        
        # Metrics
        request_duration.labels(method="GET", path="/templates").observe(time.time() - start_time)
        request_count.labels(method="GET", path="/templates", status_code=200).inc()
        
        logger.info(
            "Templates listed successfully",
            correlation_id=correlation_id,
            count=len(templates)
        )
        
        return templates
        
    except Exception as e:
        logger.error(
            "Failed to list templates",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")


@app.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific template by ID."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Getting template",
        correlation_id=correlation_id,
        template_id=template_id,
        user_id=user_id
    )
    
    try:
        # Get template
        template = db.query(Template).filter(Template.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check access - must be owner or template must be public
        if template.owner_id != user_id and not template.is_public:
            raise HTTPException(status_code=403, detail="You do not have access to this template")
        
        # Metrics
        request_duration.labels(method="GET", path="/templates/{id}").observe(time.time() - start_time)
        request_count.labels(method="GET", path="/templates/{id}", status_code=200).inc()
        
        logger.info(
            "Template retrieved successfully",
            correlation_id=correlation_id,
            template_id=template_id
        )
        
        return template
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get template",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@app.post("/templates/{template_id}/use", response_model=DiagramResponse)
async def create_diagram_from_template(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db)
):
    """Create a new diagram from a template."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating diagram from template",
        correlation_id=correlation_id,
        template_id=template_id,
        user_id=user_id
    )
    
    try:
        # Get template
        template = db.query(Template).filter(Template.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check access
        if template.owner_id != user_id and not template.is_public:
            raise HTTPException(status_code=403, detail="You do not have access to this template")
        
        # Create new diagram from template
        new_diagram = File(
            id=str(uuid.uuid4()),
            title=f"{template.name} (from template)",
            owner_id=user_id,
            file_type=template.file_type,
            canvas_data=template.canvas_data,
            note_content=template.note_content,
            current_version=1
        )
        
        db.add(new_diagram)
        
        # Increment template usage count
        template.usage_count += 1
        
        # Create initial version
        initial_version = Version(
            id=str(uuid.uuid4()),
            file_id=new_diagram.id,
            version_number=1,
            canvas_data=template.canvas_data,
            note_content=template.note_content,
            description="Created from template",
            created_by=user_id
        )
        
        db.add(initial_version)
        db.commit()
        db.refresh(new_diagram)
        
        # Metrics
        diagrams_created.inc()
        request_duration.labels(method="POST", path="/templates/{id}/use").observe(time.time() - start_time)
        request_count.labels(method="POST", path="/templates/{id}/use", status_code=201).inc()
        
        logger.info(
            "Diagram created from template successfully",
            correlation_id=correlation_id,
            template_id=template_id,
            diagram_id=new_diagram.id
        )
        
        return new_diagram
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create diagram from template",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to create diagram from template: {str(e)}")


@app.delete("/templates/{template_id}")
async def delete_template(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete a template (owner only)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Deleting template",
        correlation_id=correlation_id,
        template_id=template_id,
        user_id=user_id
    )
    
    try:
        # Get template
        template = db.query(Template).filter(Template.id == template_id).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Check ownership
        if template.owner_id != user_id:
            raise HTTPException(status_code=403, detail="Only the template owner can delete it")
        
        # Delete template
        db.delete(template)
        db.commit()
        
        # Metrics
        request_duration.labels(method="DELETE", path="/templates/{id}").observe(time.time() - start_time)
        request_count.labels(method="DELETE", path="/templates/{id}", status_code=200).inc()
        
        logger.info(
            "Template deleted successfully",
            correlation_id=correlation_id,
            template_id=template_id
        )
        
        return {"message": "Template deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete template",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete template: {str(e)}")


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
    
    # Query diagram (exclude deleted)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found or deleted",
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
    
    # Increment view count
    if diagram.view_count is None:
        diagram.view_count = 0
    diagram.view_count += 1
    diagram.last_accessed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Diagram fetched successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        view_count=diagram.view_count
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
    
    # Query diagram (exclude deleted)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found or deleted",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization - user must own the diagram OR have edit permission via share
    has_permission = False
    permission_source = None
    
    if diagram.owner_id == user_id:
        has_permission = True
        permission_source = "owner"
    else:
        # Check if user has edit access via a share token
        # Look for X-Share-Token header
        share_token = request.headers.get("X-Share-Token")
        if share_token:
            share = db.query(Share).filter(
                Share.token == share_token,
                Share.file_id == diagram_id
            ).first()
            
            if share and share.permission == "edit":
                # Check if share is still valid (not expired)
                from datetime import timezone
                if share.expires_at is None or share.expires_at > datetime.now(timezone.utc):
                    has_permission = True
                    permission_source = "share_edit"
                else:
                    logger.warning(
                        "Share token expired",
                        correlation_id=correlation_id,
                        diagram_id=diagram_id,
                        share_token=share_token[:10] + "..."
                    )
            elif share and share.permission == "view":
                logger.warning(
                    "Attempt to edit with view-only share",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id,
                    user_id=user_id,
                    share_token=share_token[:10] + "..."
                )
                raise HTTPException(status_code=403, detail="You have view-only access to this diagram")
    
    if not has_permission:
        logger.warning(
            "Unauthorized update attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="You do not have permission to update this diagram")
    
    logger.info(
        "Update authorized",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id,
        permission_source=permission_source
    )
    
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
    
    # Track who last edited the diagram
    diagram.last_edited_by = user_id
    
    # Regenerate thumbnail if canvas_data was updated
    if update_data.canvas_data is not None:
        try:
            thumbnail_url = await generate_thumbnail(diagram.id, update_data.canvas_data)
            if thumbnail_url:
                diagram.thumbnail_url = thumbnail_url
        except Exception as e:
            logger.warning(
                "Thumbnail regeneration failed, continuing without thumbnail update",
                correlation_id=correlation_id,
                diagram_id=diagram.id,
                error=str(e)
            )
    
    # Create new version with auto-incremented version number
    create_version(db, diagram, description=update_data.description, created_by=user_id)
    
    db.commit()
    db.refresh(diagram)
    
    # Update metrics
    diagrams_updated.inc()
    
    print(f"DEBUG: About to send WebSocket notification for diagram {diagram_id}")
    
    # Send WebSocket notification to collaborators
    collaboration_service_url = os.getenv("COLLABORATION_SERVICE_URL", "http://localhost:8083")
    room_id = f"file:{diagram_id}"
    
    logger.info(
        "Attempting to send WebSocket notification",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        room_id=room_id,
        collaboration_service_url=collaboration_service_url
    )
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.post(
                f"{collaboration_service_url}/broadcast/{room_id}",
                json={
                    "type": "diagram_updated",
                    "diagram_id": diagram_id,
                    "user_id": user_id,
                    "version": diagram.current_version,
                    "timestamp": datetime.utcnow().isoformat(),
                    "changes": {
                        "title": update_data.title is not None,
                        "canvas_data": update_data.canvas_data is not None,
                        "note_content": update_data.note_content is not None
                    }
                }
            )
            
            logger.info(
                "WebSocket notification sent",
                correlation_id=correlation_id,
                diagram_id=diagram_id,
                room_id=room_id,
                status_code=response.status_code
            )
    except Exception as e:
        # Don't fail the update if WebSocket notification fails
        logger.warning(
            "Failed to send WebSocket notification",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            error=str(e),
            error_type=type(e).__name__
        )
        import traceback
        logger.warning(
            "WebSocket notification traceback",
            correlation_id=correlation_id,
            traceback=traceback.format_exc()
        )
    
    logger.info(
        "Diagram updated successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id,
        new_version=diagram.current_version
    )
    
    return diagram


@app.delete("/{diagram_id}")
async def delete_diagram(
    diagram_id: str,
    request: Request,
    permanent: bool = False,
    db: Session = Depends(get_db)
):
    """Delete a diagram (soft or hard delete).
    
    Args:
        diagram_id: ID of the diagram to delete
        permanent: If True, permanently delete (hard delete). If False, move to trash (soft delete).
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    delete_type = "hard" if permanent else "soft"
    logger.info(
        f"{delete_type.capitalize()} deleting diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id,
        permanent=permanent
    )
    
    # For soft delete, only get non-deleted diagrams
    # For hard delete, get deleted diagrams (from trash)
    if permanent:
        # Hard delete: get from trash (is_deleted=True)
        diagram = db.query(File).filter(
            File.id == diagram_id,
            File.is_deleted == True
        ).first()
    else:
        # Soft delete: get active diagrams (is_deleted=False)
        diagram = db.query(File).filter(
            File.id == diagram_id,
            File.is_deleted == False
        ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            permanent=permanent
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized delete attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to delete this diagram")
    
    if permanent:
        # Hard delete: permanently remove from database
        # First, delete all versions
        versions_deleted = db.query(Version).filter(Version.file_id == diagram_id).delete()
        
        # Then delete the diagram itself
        db.delete(diagram)
        db.commit()
        
        logger.info(
            "Diagram permanently deleted",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            versions_deleted=versions_deleted
        )
        
        # Update metrics
        diagrams_updated.inc()
        
        return {
            "message": "Diagram permanently deleted",
            "id": diagram_id,
            "versions_deleted": versions_deleted
        }
    else:
        # Soft delete: set is_deleted=True and deleted_at timestamp
        diagram.is_deleted = True
        diagram.deleted_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(
            "Diagram soft deleted successfully",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            deleted_at=diagram.deleted_at.isoformat()
        )
        
        # Update metrics
        diagrams_updated.inc()
        
        return {
            "message": "Diagram moved to trash",
            "id": diagram_id,
            "deleted_at": diagram.deleted_at.isoformat()
        }


@app.post("/{diagram_id}/restore")
async def restore_diagram(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Restore a diagram from trash.
    
    Args:
        diagram_id: ID of the diagram to restore
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Restoring diagram from trash",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Get diagram from trash (is_deleted=True)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == True
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found in trash",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found in trash")
    
    # Check authorization
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized restore attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to restore this diagram")
    
    # Restore: clear is_deleted flag and deleted_at timestamp
    diagram.is_deleted = False
    diagram.deleted_at = None
    
    db.commit()
    
    logger.info(
        "Diagram restored successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Update metrics
    diagrams_updated.inc()
    
    return {
        "message": "Diagram restored from trash",
        "id": diagram_id,
        "title": diagram.title,
        "restored_at": datetime.utcnow().isoformat()
    }


@app.post("/{diagram_id}/duplicate")
async def duplicate_diagram(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Duplicate a diagram with a new UUID and fresh version history.
    
    Args:
        diagram_id: ID of the diagram to duplicate
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Duplicating diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Get original diagram (must be active, not deleted)
    original = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not original:
        logger.warning(
            "Diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization (user must have access to original)
    if original.owner_id != user_id:
        logger.warning(
            "Unauthorized duplicate attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=original.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to duplicate this diagram")
    
    # Create duplicate with new UUID
    import uuid
    duplicate_id = str(uuid.uuid4())
    
    # Append " (Copy)" to title if not already there
    duplicate_title = original.title
    if not duplicate_title.endswith(" (Copy)"):
        duplicate_title = f"{duplicate_title} (Copy)"
    
    # Create new diagram
    duplicate = File(
        id=duplicate_id,
        title=duplicate_title,
        file_type=original.file_type,
        canvas_data=original.canvas_data,  # Copy canvas data exactly
        note_content=original.note_content,  # Copy note content exactly
        owner_id=user_id,
        team_id=original.team_id,
        folder_id=original.folder_id,
        is_deleted=False,
        current_version=1,  # Fresh version history
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(duplicate)
    
    # Create initial version for duplicate
    initial_version = Version(
        id=str(uuid.uuid4()),
        file_id=duplicate_id,
        version_number=1,
        canvas_data=original.canvas_data,
        note_content=original.note_content,
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    
    db.add(initial_version)
    db.commit()
    db.refresh(duplicate)
    
    logger.info(
        "Diagram duplicated successfully",
        correlation_id=correlation_id,
        original_id=diagram_id,
        duplicate_id=duplicate_id,
        user_id=user_id
    )
    
    # Update metrics
    diagrams_created.inc()
    
    return {
        "message": "Diagram duplicated successfully",
        "original_id": diagram_id,
        "duplicate_id": duplicate_id,
        "title": duplicate.title,
        "file_type": duplicate.file_type,
        "version": duplicate.current_version,
        "created_at": duplicate.created_at.isoformat(),
        "updated_at": duplicate.updated_at.isoformat()
    }


@app.put("/{diagram_id}/move")
async def move_diagram(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Move diagram to a folder (or root if folder_id is null)."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        logger.warning(
            "Unauthorized move attempt - no user ID",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Parse request body
    try:
        body = await request.json()
        folder_id = body.get("folder_id")  # Can be null to move to root
    except Exception as e:
        logger.error(
            "Invalid request body",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail="Invalid request body")
    
    logger.info(
        "Moving diagram to folder",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    # Get diagram (only active diagrams)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found or deleted",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization - only owner can move
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized move attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to move this diagram")
    
    # If folder_id is provided, verify folder exists and user owns it
    if folder_id:
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == user_id
        ).first()
        
        if not folder:
            logger.warning(
                "Folder not found or not owned by user",
                correlation_id=correlation_id,
                folder_id=folder_id,
                user_id=user_id
            )
            raise HTTPException(status_code=404, detail="Folder not found")
    
    # Move diagram to folder (or root if folder_id is None)
    old_folder_id = diagram.folder_id
    diagram.folder_id = folder_id
    diagram.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Diagram moved successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        old_folder_id=old_folder_id,
        new_folder_id=folder_id,
        user_id=user_id
    )
    
    return {
        "message": "Diagram moved successfully",
        "id": diagram_id,
        "title": diagram.title,
        "folder_id": diagram.folder_id,
        "updated_at": diagram.updated_at.isoformat()
    }


@app.put("/{diagram_id}/star")
async def star_diagram(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Toggle star/favorite status for a diagram."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        logger.warning(
            "Unauthorized star attempt - no user ID",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    logger.info(
        "Toggling star status",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Get diagram (only active diagrams)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found or deleted",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization - only owner can star/unstar
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized star attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to star this diagram")
    
    # Toggle star status
    old_status = diagram.is_starred
    diagram.is_starred = not diagram.is_starred
    diagram.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Star status toggled successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        old_status=old_status,
        new_status=diagram.is_starred,
        user_id=user_id
    )
    
    return {
        "message": f"Diagram {'starred' if diagram.is_starred else 'unstarred'} successfully",
        "id": diagram_id,
        "title": diagram.title,
        "is_starred": diagram.is_starred,
        "updated_at": diagram.updated_at.isoformat()
    }


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


# ==========================================
# SHARE ENDPOINTS
# ==========================================

@app.post("/{diagram_id}/share")
async def create_share_link(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a public share link for a diagram.
    
    Request body (optional):
    {
        "permission": "view" | "edit",  // Default: "view"
        "is_public": true | false,       // Default: true
        "password": "optional_password", // For password-protected shares
        "expires_in_days": 7             // Optional expiration
    }
    
    Returns:
    {
        "share_id": "uuid",
        "token": "unique_token",
        "share_url": "http://localhost:3000/shared/{token}",
        "permission": "view",
        "is_public": true,
        "expires_at": "2025-12-30T00:00:00Z" or null
    }
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        logger.warning(
            "Unauthorized share creation attempt - no user ID",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating share link",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Get diagram (only active diagrams can be shared)
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Share creation failed - diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization (only owner can share)
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized share creation attempt",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            user_id=user_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Only the owner can share this diagram")
    
    # Parse request body (optional)
    body = {}
    try:
        body = await request.json()
    except:
        pass  # No body provided, use defaults
    
    permission = body.get("permission", "view")
    is_public = body.get("is_public", True)
    password = body.get("password")
    expires_in_days = body.get("expires_in_days")
    
    # Validate permission
    if permission not in ["view", "edit"]:
        raise HTTPException(status_code=400, detail="Permission must be 'view' or 'edit'")
    
    # Generate unique share token
    import secrets
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = None
    if expires_in_days:
        from datetime import timedelta, timezone
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
    
    # Hash password if provided
    password_hash = None
    if password:
        import bcrypt
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create share record
    import uuid
    from datetime import timezone as tz
    share = Share(
        id=str(uuid.uuid4()),
        file_id=diagram_id,
        token=token,
        permission=permission,
        is_public=is_public,
        password_hash=password_hash,
        expires_at=expires_at,
        view_count=0,
        created_by=user_id,
        created_at=datetime.now(tz.utc)
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    # Build share URL
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    share_url = f"{frontend_url}/shared/{token}"
    
    logger.info(
        "Share link created successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        share_id=share.id,
        token=token[:10] + "...",
        permission=permission,
        is_public=is_public
    )
    
    return {
        "share_id": share.id,
        "token": token,
        "share_url": share_url,
        "permission": permission,
        "is_public": is_public,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "has_password": password is not None
    }


@app.get("/shared/{token}")
async def get_shared_diagram(
    token: str,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Access a shared diagram via its public token.
    
    Query params:
    - password: Optional password for password-protected shares
    
    Returns:
    {
        "id": "diagram_id",
        "title": "Diagram Title",
        "type": "canvas",
        "canvas_data": {...},
        "note_content": "...",
        "permission": "view",
        "owner": {...}
    }
    """
    logger.info(
        "Accessing shared diagram",
        token=token[:10] + "..."
    )
    
    # Find share by token
    share = db.query(Share).filter(Share.token == token).first()
    
    if not share:
        logger.warning(
            "Share not found",
            token=token[:10] + "..."
        )
        raise HTTPException(status_code=404, detail="Share link not found")
    
    # Get current time for timezone-aware operations
    from datetime import timezone
    now_utc = datetime.now(timezone.utc)
    
    # Check if expired
    if share.expires_at:
        if share.expires_at < now_utc:
            logger.warning("Share link expired", token=token[:10] + "...")
            raise HTTPException(status_code=410, detail="Share link has expired")
    
    # Check password if required
    if share.password_hash:
        if not password:
            raise HTTPException(status_code=401, detail="Password required")
        
        import bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), share.password_hash.encode('utf-8')):
            logger.warning(
                "Invalid password for shared diagram",
                token=token[:10] + "..."
            )
            raise HTTPException(status_code=401, detail="Invalid password")
    
    # Get diagram
    diagram = db.query(File).filter(
        File.id == share.file_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Shared diagram not found or deleted",
            token=token[:10] + "...",
            file_id=share.file_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found or has been deleted")
    
    # Update view count and last accessed
    share.view_count = (share.view_count or 0) + 1
    share.last_accessed_at = now_utc
    db.commit()
    db.refresh(share)  # Refresh to get the latest data
    
    # Get owner info
    owner = db.query(User).filter(User.id == diagram.owner_id).first()
    
    logger.info(
        "Shared diagram accessed successfully",
        token=token[:10] + "...",
        diagram_id=diagram.id,
        view_count=share.view_count
    )
    
    return {
        "id": diagram.id,
        "title": diagram.title,
        "type": diagram.file_type,
        "canvas_data": diagram.canvas_data,
        "note_content": diagram.note_content,
        "permission": share.permission,
        "is_public": share.is_public,
        "view_count": share.view_count,
        "last_accessed_at": share.last_accessed_at.isoformat() if share.last_accessed_at else None,
        "owner": {
            "id": owner.id if owner else None,
            "full_name": owner.full_name if owner else "Unknown",
            "email": owner.email if owner else None
        },
        "created_at": diagram.created_at.isoformat(),
        "updated_at": diagram.updated_at.isoformat()
    }


@app.delete("/{diagram_id}/share/{share_id}")
async def revoke_share_link(
    diagram_id: str,
    share_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Revoke a share link for a diagram.
    
    This permanently deletes the share record, making the share link inaccessible.
    
    Parameters:
    - diagram_id: UUID of the diagram
    - share_id: UUID of the share to revoke
    
    Returns:
    {
        "message": "Share link revoked successfully",
        "share_id": "uuid"
    }
    
    Errors:
    - 404: Share not found
    - 403: Not authorized to revoke this share
    """
    correlation_id = request.headers.get("X-Correlation-ID", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Revoking share link",
        correlation_id=correlation_id,
        user_id=user_id,
        diagram_id=diagram_id,
        share_id=share_id
    )
    
    # Get the diagram
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Diagram not found for share revocation",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check if user owns the diagram
    if diagram.owner_id != user_id:
        logger.warning(
            "User not authorized to revoke share",
            correlation_id=correlation_id,
            user_id=user_id,
            diagram_id=diagram_id,
            owner_id=diagram.owner_id
        )
        raise HTTPException(status_code=403, detail="Not authorized to revoke this share")
    
    # Get the share
    share = db.query(Share).filter(
        Share.id == share_id,
        Share.file_id == diagram_id
    ).first()
    
    if not share:
        logger.warning(
            "Share not found for revocation",
            correlation_id=correlation_id,
            share_id=share_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Share link not found")
    
    # Delete the share
    db.delete(share)
    db.commit()
    
    logger.info(
        "Share link revoked successfully",
        correlation_id=correlation_id,
        share_id=share_id,
        diagram_id=diagram_id
    )
    
    return {
        "message": "Share link revoked successfully",
        "share_id": share_id
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DIAGRAM_SERVICE_PORT", "8082")))

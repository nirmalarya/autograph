"""Diagram Service - Diagram CRUD and storage."""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, Response
from datetime import datetime, timedelta, timezone
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
import gzip
import base64

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST

# Import database and models
from .database import get_db
from .models import File, User, Version, Folder, Share, Template, Comment, Mention, CommentReaction, ExportHistory, Team

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


# Compression utilities for version history
def compress_data(data: Any) -> tuple[str, int, int]:
    """Compress data using gzip and return base64-encoded string with sizes.
    
    Args:
        data: Any JSON-serializable data
        
    Returns:
        Tuple of (compressed_base64_string, original_size, compressed_size)
    """
    if data is None:
        return None, 0, 0
    
    # Convert to JSON string
    json_str = json.dumps(data, separators=(',', ':'))  # No whitespace
    original_bytes = json_str.encode('utf-8')
    original_size = len(original_bytes)
    
    # Compress with gzip (level 9 = maximum compression)
    compressed_bytes = gzip.compress(original_bytes, compresslevel=9)
    compressed_size = len(compressed_bytes)
    
    # Base64 encode for storage in TEXT column
    compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
    
    return compressed_b64, original_size, compressed_size


def decompress_data(compressed_b64: str) -> Any:
    """Decompress base64-encoded gzipped data.
    
    Args:
        compressed_b64: Base64-encoded gzipped JSON string
        
    Returns:
        Original data (parsed JSON)
    """
    if not compressed_b64:
        return None
    
    # Decode base64
    compressed_bytes = base64.b64decode(compressed_b64)
    
    # Decompress
    original_bytes = gzip.decompress(compressed_bytes)
    
    # Parse JSON
    json_str = original_bytes.decode('utf-8')
    return json.loads(json_str)


def compress_version(version: Version, db: Session) -> dict:
    """Compress a version's content and update database.
    
    Args:
        version: Version object to compress
        db: Database session
        
    Returns:
        Dict with compression statistics
    """
    if version.is_compressed:
        return {"status": "already_compressed", "version_id": version.id}
    
    total_original_size = 0
    total_compressed_size = 0
    
    # Compress canvas_data if present
    if version.canvas_data:
        compressed_canvas, canvas_orig, canvas_comp = compress_data(version.canvas_data)
        version.compressed_canvas_data = compressed_canvas
        total_original_size += canvas_orig
        total_compressed_size += canvas_comp
        # Clear original data to save space
        version.canvas_data = None
    
    # Compress note_content if present
    if version.note_content:
        compressed_note, note_orig, note_comp = compress_data(version.note_content)
        version.compressed_note_content = compressed_note
        total_original_size += note_orig
        total_compressed_size += note_comp
        # Clear original data to save space
        version.note_content = None
    
    # Update compression metadata
    version.is_compressed = True
    version.original_size = total_original_size
    version.compressed_size = total_compressed_size
    version.compression_ratio = total_compressed_size / total_original_size if total_original_size > 0 else 0.0
    version.compressed_at = datetime.now(timezone.utc)
    
    db.commit()
    
    return {
        "status": "compressed",
        "version_id": version.id,
        "original_size": total_original_size,
        "compressed_size": total_compressed_size,
        "compression_ratio": version.compression_ratio,
        "savings_bytes": total_original_size - total_compressed_size,
        "savings_percent": ((total_original_size - total_compressed_size) / total_original_size * 100) if total_original_size > 0 else 0
    }


def get_version_content(version: Version) -> tuple[Any, Optional[str]]:
    """Get version content, decompressing if necessary.
    
    Args:
        version: Version object
        
    Returns:
        Tuple of (canvas_data, note_content)
    """
    if version.is_compressed:
        # Decompress data
        canvas_data = decompress_data(version.compressed_canvas_data) if version.compressed_canvas_data else None
        note_content = decompress_data(version.compressed_note_content) if version.compressed_note_content else None
    else:
        # Use original data
        canvas_data = version.canvas_data
        note_content = version.note_content
    
    return canvas_data, note_content


def calculate_version_size(version: Version) -> int:
    """Calculate the size of a version in bytes.
    
    Args:
        version: Version object
        
    Returns:
        Size in bytes
    """
    if version.is_compressed and version.original_size:
        # For compressed versions, use the stored original_size
        return version.original_size
    
    # Get the actual content
    canvas_data, note_content = get_version_content(version)
    
    # Calculate size by JSON-encoding the data
    size = 0
    if canvas_data:
        size += len(json.dumps(canvas_data, separators=(',', ':')).encode('utf-8'))
    if note_content:
        size += len(note_content.encode('utf-8'))
    
    return size


def format_size_human_readable(size_bytes: int) -> dict:
    """Format size in bytes to human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Dict with size_bytes, size_kb, size_mb, and display_size
    """
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024
    
    if size_mb >= 1:
        display_size = f"{size_mb:.2f} MB"
    elif size_kb >= 1:
        display_size = f"{size_kb:.2f} KB"
    else:
        display_size = f"{size_bytes} B"
    
    return {
        "size_bytes": size_bytes,
        "size_kb": round(size_kb, 2),
        "size_mb": round(size_mb, 2),
        "display_size": display_size
    }


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


def calculate_diagram_size(diagram: File) -> int:
    """Calculate total size of diagram in bytes (canvas_data + note_content)."""
    size = 0
    
    # Calculate canvas_data size
    if diagram.canvas_data:
        # Convert JSONB to JSON string and get byte size
        canvas_json = json.dumps(diagram.canvas_data)
        size += len(canvas_json.encode('utf-8'))
    
    # Calculate note_content size
    if diagram.note_content:
        size += len(diagram.note_content.encode('utf-8'))
    
    return size


def enrich_diagram_response(diagram: File) -> Dict[str, Any]:
    """Enrich diagram with calculated fields like size."""
    diagram_dict = DiagramResponse.model_validate(diagram).model_dump()
    diagram_dict['size_bytes'] = calculate_diagram_size(diagram)
    return diagram_dict


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
    
    # Apply full-text search with fuzzy matching and advanced filters
    if search:
        # Parse advanced search filters (e.g., "type:canvas database", "author:john aws")
        import re
        
        # Extract filter keywords (format: "keyword:value")
        filter_pattern = r'(\w+):(\S+)'
        filters = re.findall(filter_pattern, search)
        
        # Remove filters from search query to get plain search terms
        search_terms = re.sub(filter_pattern, '', search).strip()
        
        # Apply keyword filters
        for filter_key, filter_value in filters:
            if filter_key.lower() == 'type':
                # Filter by file type
                if filter_value.lower() in ['canvas', 'note', 'mixed']:
                    query = query.filter(File.file_type == filter_value.lower())
            elif filter_key.lower() == 'author':
                # Filter by author (owner email)
                # Join with users table to search by email/name
                from .models import User
                user_subquery = db.query(User.id).filter(
                    or_(
                        User.email.ilike(f'%{filter_value}%'),
                        User.full_name.ilike(f'%{filter_value}%')
                    )
                ).subquery()
                query = query.filter(File.owner_id.in_(user_subquery))
            elif filter_key.lower() == 'tag':
                # Filter by tag using JSON contains operator
                # PostgreSQL: tags @> '["value"]' checks if JSON array contains the value
                from sqlalchemy.dialects.postgresql import JSONB
                from sqlalchemy import cast
                query = query.filter(
                    cast(File.tags, JSONB).op('@>')(f'["{filter_value}"]')
                )
            elif filter_key.lower() == 'after':
                # Filter by date (created after)
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(filter_value)
                    query = query.filter(File.created_at >= date_obj)
                except ValueError:
                    pass  # Invalid date format, skip filter
            elif filter_key.lower() == 'before':
                # Filter by date (created before)
                try:
                    from datetime import datetime
                    date_obj = datetime.fromisoformat(filter_value)
                    query = query.filter(File.created_at <= date_obj)
                except ValueError:
                    pass  # Invalid date format, skip filter
        
        # If there are remaining search terms (after filters removed), apply search
        if search_terms:
            # Exact match pattern for traditional search
            search_pattern = f"%{search_terms}%"
            
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
                    func.similarity(File.title, search_terms) >= similarity_threshold,
                    func.similarity(File.note_content, search_terms) >= similarity_threshold
                )
            )
            
            # Order fuzzy search results by relevance (similarity score)
            # Higher similarity scores appear first
            query = query.order_by(
                func.greatest(
                    func.similarity(File.title, search_terms),
                    func.similarity(func.coalesce(File.note_content, ''), search_terms)
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
                'last_accessed_at': File.last_accessed_at,
                'last_activity': File.last_activity,
                'last_activity_at': File.last_activity  # Alias
                # Note: size_bytes is not a column, it's calculated dynamically in enrich_diagram_response
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
        "diagrams": [enrich_diagram_response(d) for d in diagrams],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


@app.get("/recent")
async def list_recent_diagrams(
    request: Request,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List recently accessed diagrams (last 10 by default).
    
    This endpoint returns diagrams sorted by last_accessed_at timestamp,
    showing the most recently viewed diagrams first.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    # Validate limit parameter
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    logger.info(
        "Listing recent diagrams",
        correlation_id=correlation_id,
        user_id=user_id,
        limit=limit
    )
    
    # Query recent diagrams
    # Filter by owner and not deleted
    # Only include diagrams that have been accessed (last_accessed_at is not null)
    # Sort by last_accessed_at descending (most recent first)
    diagrams = db.query(File).filter(
        File.owner_id == user_id,
        File.is_deleted == False,
        File.last_accessed_at.isnot(None)
    ).order_by(
        File.last_accessed_at.desc()
    ).limit(limit).all()
    
    logger.info(
        "Recent diagrams listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        returned=len(diagrams)
    )
    
    return {
        "diagrams": [enrich_diagram_response(d) for d in diagrams],
        "total": len(diagrams),
        "limit": limit
    }


@app.get("/starred")
async def list_starred_diagrams(
    request: Request,
    db: Session = Depends(get_db)
):
    """List starred/favorited diagrams for the current user.
    
    This endpoint returns all diagrams where is_starred = True,
    showing the user's favorite diagrams.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing starred diagrams",
        correlation_id=correlation_id,
        user_id=user_id
    )
    
    # Query starred diagrams
    # Filter by owner, not deleted, and is_starred = True
    # Sort by updated_at descending (most recently updated first)
    diagrams = db.query(File).filter(
        File.owner_id == user_id,
        File.is_deleted == False,
        File.is_starred == True
    ).order_by(
        File.updated_at.desc()
    ).all()
    
    logger.info(
        "Starred diagrams listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        returned=len(diagrams)
    )
    
    return {
        "diagrams": [enrich_diagram_response(d) for d in diagrams],
        "total": len(diagrams)
    }


@app.get("/trash")
async def list_trash_diagrams(
    request: Request,
    db: Session = Depends(get_db)
):
    """List deleted diagrams in trash for the current user.
    
    This endpoint returns all diagrams where is_deleted = True,
    showing diagrams that can be restored within 30 days.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing trash diagrams",
        correlation_id=correlation_id,
        user_id=user_id
    )
    
    # Query deleted diagrams (trash)
    # Filter by owner and is_deleted = True
    # Sort by deleted_at descending (most recently deleted first)
    diagrams = db.query(File).filter(
        File.owner_id == user_id,
        File.is_deleted == True
    ).order_by(
        File.deleted_at.desc()
    ).all()
    
    logger.info(
        "Trash diagrams listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        returned=len(diagrams)
    )
    
    return {
        "diagrams": [enrich_diagram_response(d) for d in diagrams],
        "total": len(diagrams)
    }


@app.get("/shared-with-me")
async def list_shared_with_me(
    request: Request,
    db: Session = Depends(get_db)
):
    """List diagrams shared with the current user.
    
    This endpoint returns diagrams that other users have explicitly shared
    with the current user via user-specific shares.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing shared with me diagrams",
        correlation_id=correlation_id,
        user_id=user_id
    )
    
    # Query diagrams shared with this user
    # Join shares table with files table
    # Filter by shared_with_user_id = current user
    # Only include non-deleted files
    shared_diagrams = db.query(File).join(
        Share, File.id == Share.file_id
    ).filter(
        Share.shared_with_user_id == user_id,
        File.is_deleted == False
    ).order_by(
        Share.created_at.desc()
    ).all()
    
    # For each diagram, get the share info (permission level, owner)
    result = []
    for diagram in shared_diagrams:
        # Get the share info
        share = db.query(Share).filter(
            Share.file_id == diagram.id,
            Share.shared_with_user_id == user_id
        ).first()
        
        # Get owner info
        owner = db.query(User).filter(User.id == diagram.owner_id).first()
        
        diagram_data = enrich_diagram_response(diagram)
        diagram_data['permission'] = share.permission if share else 'view'
        diagram_data['owner_email'] = owner.email if owner else 'Unknown'
        diagram_data['shared_at'] = share.created_at.isoformat() if share else None
        
        result.append(diagram_data)
    
    logger.info(
        "Shared with me diagrams listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        returned=len(result)
    )
    
    return {
        "diagrams": result,
        "total": len(result)
    }


@app.get("/team")
async def list_team_files(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all diagrams in team workspaces where user is a member.
    
    This endpoint returns diagrams that belong to teams where the current
    user is either the owner or a member.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing team files",
        correlation_id=correlation_id,
        user_id=user_id
    )
    
    # Get all teams where user is the owner
    user_teams = db.query(Team).filter(
        Team.owner_id == user_id
    ).all()
    
    team_ids = [team.id for team in user_teams]
    
    if not team_ids:
        # User is not part of any team
        logger.info(
            "No teams found for user",
            correlation_id=correlation_id,
            user_id=user_id
        )
        return {
            "diagrams": [],
            "total": 0
        }
    
    # Query all files that belong to user's teams
    team_files = db.query(File).filter(
        File.team_id.in_(team_ids),
        File.is_deleted == False
    ).order_by(
        File.updated_at.desc()
    ).all()
    
    # Enrich each diagram with owner info
    result = []
    for diagram in team_files:
        # Get owner info
        owner = db.query(User).filter(User.id == diagram.owner_id).first()
        
        diagram_data = enrich_diagram_response(diagram)
        diagram_data['owner_email'] = owner.email if owner else 'Unknown'
        
        # Get team name
        team = db.query(Team).filter(Team.id == diagram.team_id).first()
        diagram_data['team_name'] = team.name if team else 'Unknown Team'
        
        result.append(diagram_data)
    
    logger.info(
        "Team files listed successfully",
        correlation_id=correlation_id,
        user_id=user_id,
        returned=len(result)
    )
    
    return {
        "diagrams": result,
        "total": len(result)
    }


# Pydantic models for request/response with validation
class CreateDiagramRequest(BaseModel):
    """Request model for creating a diagram."""
    title: str
    file_type: str = "canvas"  # canvas, note, mixed
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    folder_id: Optional[str] = None
    tags: Optional[list[str]] = []
    
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
    export_count: int = 0  # Number of times diagram has been exported
    collaborator_count: int = 1  # Number of collaborators (owner + shared users)
    comment_count: int = 0  # Number of comments on diagram
    current_version: int
    version_count: int = 1  # Total number of versions
    last_edited_by: Optional[str] = None
    tags: Optional[list] = []
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None  # Last activity (view, edit, comment)
    size_bytes: Optional[int] = None  # Total size in bytes (canvas_data + note_content)
    
    class Config:
        from_attributes = True


class UpdateDiagramRequest(BaseModel):
    """Request model for updating a diagram."""
    title: Optional[str] = None
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    description: Optional[str] = None  # Version description
    expected_version: Optional[int] = None  # For optimistic locking
    tags: Optional[list[str]] = None
    
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


def create_version_snapshot(db: Session, file: File, description: Optional[str] = None, created_by: Optional[str] = None) -> Version:
    """Create a new version for a file with auto-incremented version number."""
    # Get the highest version number for this file (use max, not count, for consistency)
    latest_version = db.query(Version).filter(
        Version.file_id == file.id
    ).order_by(Version.version_number.desc()).first()
    next_version_number = (latest_version.version_number + 1) if latest_version else 1
    
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
    
    # Update file's current_version and version_count
    file.current_version = next_version_number
    file.version_count = next_version_number
    
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
        folder_id=diagram.folder_id,
        tags=diagram.tags or [],
        last_activity=datetime.utcnow()  # Set initial last_activity
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
    create_version_snapshot(db, new_diagram, description="Initial version", created_by=user_id)
    
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
    
    return enrich_diagram_response(new_diagram)


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
            current_version=1,
            last_activity=datetime.utcnow()  # Set initial last_activity
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


# ============================================================================
# FOLDER ENDPOINTS
# ============================================================================

class CreateFolderRequest(BaseModel):
    """Request model for creating a folder."""
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class UpdateFolderRequest(BaseModel):
    """Request model for updating a folder."""
    name: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None

class FolderResponse(BaseModel):
    """Response model for folder."""
    id: str
    name: str
    owner_id: str
    parent_id: Optional[str]
    color: Optional[str]
    icon: Optional[str]
    created_at: datetime
    updated_at: datetime
    subfolders: Optional[list] = []
    file_count: Optional[int] = 0

    class Config:
        from_attributes = True


@app.post("/folders", status_code=201)
async def create_folder(
    request: Request,
    folder_request: CreateFolderRequest,
    db: Session = Depends(get_db)
):
    """Create a new folder."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating folder",
        correlation_id=correlation_id,
        user_id=user_id,
        folder_name=folder_request.name
    )
    
    try:
        # Validate parent folder exists if provided
        if folder_request.parent_id:
            parent = db.query(Folder).filter(
                Folder.id == folder_request.parent_id,
                Folder.owner_id == user_id
            ).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")
        
        # Create folder
        folder = Folder(
            id=str(uuid.uuid4()),
            name=folder_request.name,
            owner_id=user_id,
            parent_id=folder_request.parent_id,
            color=folder_request.color,
            icon=folder_request.icon
        )
        
        db.add(folder)
        db.commit()
        db.refresh(folder)
        
        # Get file count
        file_count = db.query(File).filter(
            File.folder_id == folder.id,
            File.is_deleted == False
        ).count()
        
        # Metrics
        request_duration.labels(method="POST", path="/folders").observe(time.time() - start_time)
        request_count.labels(method="POST", path="/folders", status_code=201).inc()
        
        logger.info(
            "Folder created successfully",
            correlation_id=correlation_id,
            folder_id=folder.id
        )
        
        return {
            "id": folder.id,
            "name": folder.name,
            "owner_id": folder.owner_id,
            "parent_id": folder.parent_id,
            "color": folder.color,
            "icon": folder.icon,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "subfolders": [],
            "file_count": file_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create folder",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")


@app.get("/folders")
async def list_folders(
    request: Request,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List folders for the current user."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Listing folders",
        correlation_id=correlation_id,
        user_id=user_id,
        parent_id=parent_id
    )
    
    try:
        # Query folders
        query = db.query(Folder).filter(Folder.owner_id == user_id)
        
        # Filter by parent
        if parent_id:
            query = query.filter(Folder.parent_id == parent_id)
        else:
            # Root folders only
            query = query.filter(Folder.parent_id == None)
        
        folders = query.order_by(Folder.name).all()
        
        # Build response with subfolder counts and file counts
        result = []
        for folder in folders:
            subfolder_count = db.query(Folder).filter(Folder.parent_id == folder.id).count()
            file_count = db.query(File).filter(
                File.folder_id == folder.id,
                File.is_deleted == False
            ).count()
            
            result.append({
                "id": folder.id,
                "name": folder.name,
                "owner_id": folder.owner_id,
                "parent_id": folder.parent_id,
                "color": folder.color,
                "icon": folder.icon,
                "created_at": folder.created_at,
                "updated_at": folder.updated_at,
                "subfolder_count": subfolder_count,
                "file_count": file_count
            })
        
        # Metrics
        request_duration.labels(method="GET", path="/folders").observe(time.time() - start_time)
        request_count.labels(method="GET", path="/folders", status_code=200).inc()
        
        logger.info(
            "Folders listed successfully",
            correlation_id=correlation_id,
            count=len(result)
        )
        
        return {"folders": result, "total": len(result)}
        
    except Exception as e:
        logger.error(
            "Failed to list folders",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to list folders: {str(e)}")


@app.get("/folders/{folder_id}")
async def get_folder(
    request: Request,
    folder_id: str,
    db: Session = Depends(get_db)
):
    """Get a folder by ID with its contents."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Getting folder",
        correlation_id=correlation_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    try:
        # Get folder
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == user_id
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Get subfolders
        subfolders = db.query(Folder).filter(Folder.parent_id == folder_id).all()
        subfolder_list = [{
            "id": sf.id,
            "name": sf.name,
            "color": sf.color,
            "icon": sf.icon,
            "created_at": sf.created_at,
            "updated_at": sf.updated_at
        } for sf in subfolders]
        
        # Get files in folder
        files = db.query(File).filter(
            File.folder_id == folder_id,
            File.is_deleted == False
        ).order_by(File.updated_at.desc()).all()
        
        file_list = [{
            "id": f.id,
            "title": f.title,
            "file_type": f.file_type,
            "is_starred": f.is_starred,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
            "last_accessed_at": f.last_accessed_at
        } for f in files]
        
        # Metrics
        request_duration.labels(method="GET", path="/folders/{id}").observe(time.time() - start_time)
        request_count.labels(method="GET", path="/folders/{id}", status_code=200).inc()
        
        logger.info(
            "Folder retrieved successfully",
            correlation_id=correlation_id,
            folder_id=folder_id,
            subfolder_count=len(subfolder_list),
            file_count=len(file_list)
        )
        
        return {
            "id": folder.id,
            "name": folder.name,
            "owner_id": folder.owner_id,
            "parent_id": folder.parent_id,
            "color": folder.color,
            "icon": folder.icon,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "subfolders": subfolder_list,
            "files": file_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get folder",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get folder: {str(e)}")


@app.put("/folders/{folder_id}")
async def update_folder(
    request: Request,
    folder_id: str,
    folder_request: UpdateFolderRequest,
    db: Session = Depends(get_db)
):
    """Update a folder."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Updating folder",
        correlation_id=correlation_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    try:
        # Get folder
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == user_id
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Validate parent folder if provided
        if folder_request.parent_id:
            # Can't be its own parent
            if folder_request.parent_id == folder_id:
                raise HTTPException(status_code=400, detail="Folder cannot be its own parent")
            
            # Check parent exists and owned by user
            parent = db.query(Folder).filter(
                Folder.id == folder_request.parent_id,
                Folder.owner_id == user_id
            ).first()
            if not parent:
                raise HTTPException(status_code=404, detail="Parent folder not found")
            
            # Check for circular reference (parent can't be a child of this folder)
            def is_descendant(folder_id, potential_ancestor_id, db):
                """Check if potential_ancestor_id is a descendant of folder_id."""
                if potential_ancestor_id == folder_id:
                    return True
                parent = db.query(Folder).filter(Folder.id == potential_ancestor_id).first()
                if parent and parent.parent_id:
                    return is_descendant(folder_id, parent.parent_id, db)
                return False
            
            if is_descendant(folder_id, folder_request.parent_id, db):
                raise HTTPException(status_code=400, detail="Cannot create circular folder reference")
        
        # Update fields
        if folder_request.name is not None:
            folder.name = folder_request.name
        if folder_request.parent_id is not None:
            folder.parent_id = folder_request.parent_id
        if folder_request.color is not None:
            folder.color = folder_request.color
        if folder_request.icon is not None:
            folder.icon = folder_request.icon
        
        db.commit()
        db.refresh(folder)
        
        # Get file count
        file_count = db.query(File).filter(
            File.folder_id == folder.id,
            File.is_deleted == False
        ).count()
        
        # Metrics
        request_duration.labels(method="PUT", path="/folders/{id}").observe(time.time() - start_time)
        request_count.labels(method="PUT", path="/folders/{id}", status_code=200).inc()
        
        logger.info(
            "Folder updated successfully",
            correlation_id=correlation_id,
            folder_id=folder_id
        )
        
        return {
            "id": folder.id,
            "name": folder.name,
            "owner_id": folder.owner_id,
            "parent_id": folder.parent_id,
            "color": folder.color,
            "icon": folder.icon,
            "created_at": folder.created_at,
            "updated_at": folder.updated_at,
            "file_count": file_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to update folder",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to update folder: {str(e)}")


@app.delete("/folders/{folder_id}")
async def delete_folder(
    request: Request,
    folder_id: str,
    db: Session = Depends(get_db)
):
    """Delete a folder (must be empty)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Deleting folder",
        correlation_id=correlation_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    try:
        # Get folder
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == user_id
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Check if folder has subfolders
        subfolder_count = db.query(Folder).filter(Folder.parent_id == folder_id).count()
        if subfolder_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete folder with subfolders")
        
        # Check if folder has files
        file_count = db.query(File).filter(
            File.folder_id == folder_id,
            File.is_deleted == False
        ).count()
        if file_count > 0:
            raise HTTPException(status_code=400, detail="Cannot delete folder with files")
        
        # Delete folder
        db.delete(folder)
        db.commit()
        
        # Metrics
        request_duration.labels(method="DELETE", path="/folders/{id}").observe(time.time() - start_time)
        request_count.labels(method="DELETE", path="/folders/{id}", status_code=200).inc()
        
        logger.info(
            "Folder deleted successfully",
            correlation_id=correlation_id,
            folder_id=folder_id
        )
        
        return {"message": "Folder deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to delete folder",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete folder: {str(e)}")


@app.get("/folders/{folder_id}/breadcrumbs")
async def get_folder_breadcrumbs(
    request: Request,
    folder_id: str,
    db: Session = Depends(get_db)
):
    """Get breadcrumb path for a folder (from root to current folder)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Getting folder breadcrumbs",
        correlation_id=correlation_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    try:
        # Get folder
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.owner_id == user_id
        ).first()
        
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        
        # Build breadcrumb path
        breadcrumbs = []
        current = folder
        
        while current:
            breadcrumbs.insert(0, {
                "id": current.id,
                "name": current.name,
                "color": current.color,
                "icon": current.icon
            })
            
            # Get parent
            if current.parent_id:
                current = db.query(Folder).filter(Folder.id == current.parent_id).first()
            else:
                current = None
        
        # Metrics
        request_duration.labels(method="GET", path="/folders/{id}/breadcrumbs").observe(time.time() - start_time)
        request_count.labels(method="GET", path="/folders/{id}/breadcrumbs", status_code=200).inc()
        
        logger.info(
            "Folder breadcrumbs retrieved successfully",
            correlation_id=correlation_id,
            folder_id=folder_id,
            depth=len(breadcrumbs)
        )
        
        return {"breadcrumbs": breadcrumbs}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get folder breadcrumbs",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to get folder breadcrumbs: {str(e)}")


@app.put("/{diagram_id}/folder")
async def move_diagram_to_folder(
    request: Request,
    diagram_id: str,
    folder_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Move a diagram to a folder (or remove from folder if folder_id is None)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    # Get user ID from header
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Moving diagram to folder",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        folder_id=folder_id,
        user_id=user_id
    )
    
    try:
        # Get diagram
        diagram = db.query(File).filter(
            File.id == diagram_id,
            File.owner_id == user_id,
            File.is_deleted == False
        ).first()
        
        if not diagram:
            raise HTTPException(status_code=404, detail="Diagram not found")
        
        # Validate folder if provided
        if folder_id:
            folder = db.query(Folder).filter(
                Folder.id == folder_id,
                Folder.owner_id == user_id
            ).first()
            if not folder:
                raise HTTPException(status_code=404, detail="Folder not found")
        
        # Update diagram folder
        diagram.folder_id = folder_id
        db.commit()
        
        # Metrics
        request_duration.labels(method="PUT", path="/{id}/folder").observe(time.time() - start_time)
        request_count.labels(method="PUT", path="/{id}/folder", status_code=200).inc()
        
        logger.info(
            "Diagram moved to folder successfully",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            folder_id=folder_id
        )
        
        return {"message": "Diagram moved successfully", "folder_id": folder_id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to move diagram to folder",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to move diagram to folder: {str(e)}")


@app.get("/{diagram_id}")
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
    diagram.last_activity = datetime.utcnow()  # Update last activity on view
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Diagram fetched successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        view_count=diagram.view_count
    )
    
    return enrich_diagram_response(diagram)


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
    
    # Major edit detection: Check if 10+ elements were deleted
    # IMPORTANT: Must check BEFORE updating diagram.canvas_data
    is_major_edit = False
    version_description = "Auto-save"
    
    if update_data.canvas_data is not None and diagram.canvas_data is not None:
        # Count elements in old and new canvas data
        old_canvas = diagram.canvas_data if isinstance(diagram.canvas_data, dict) else {}
        new_canvas = update_data.canvas_data if isinstance(update_data.canvas_data, dict) else {}
        
        # Try different common keys for elements (shapes, elements, objects, etc.)
        old_count = 0
        new_count = 0
        
        for key in ['shapes', 'elements', 'objects', 'nodes', 'items']:
            if key in old_canvas and isinstance(old_canvas[key], list):
                old_count = len(old_canvas[key])
                break
        
        for key in ['shapes', 'elements', 'objects', 'nodes', 'items']:
            if key in new_canvas and isinstance(new_canvas[key], list):
                new_count = len(new_canvas[key])
                break
        
        # If 10+ elements were deleted, mark as major edit
        if old_count - new_count >= 10:
            is_major_edit = True
            version_description = "Major edit"
            logger.info(
                "Major edit detected - 10+ elements deleted",
                correlation_id=correlation_id,
                diagram_id=diagram_id,
                old_count=old_count,
                new_count=new_count,
                deleted_count=old_count - new_count
            )
    
    # Update diagram fields
    if update_data.title is not None:
        diagram.title = update_data.title
    if update_data.canvas_data is not None:
        diagram.canvas_data = update_data.canvas_data
    if update_data.note_content is not None:
        diagram.note_content = update_data.note_content
    if update_data.tags is not None:
        diagram.tags = update_data.tags
    
    # Track who last edited the diagram
    diagram.last_edited_by = user_id
    
    # Update last activity timestamp
    diagram.last_activity = datetime.utcnow()
    
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
    
    # Auto-versioning: Create a version if 5+ minutes have passed OR if major edit detected
    should_create_version = False
    if is_major_edit:
        # Major edit - always create version immediately
        should_create_version = True
    elif diagram.last_auto_versioned_at is None:
        # First time - create initial version
        should_create_version = True
    else:
        # Check if 5 minutes have passed
        time_since_last_version = datetime.utcnow() - diagram.last_auto_versioned_at.replace(tzinfo=None)
        if time_since_last_version.total_seconds() >= 300:  # 5 minutes = 300 seconds
            should_create_version = True
    
    if should_create_version and (update_data.canvas_data is not None or update_data.note_content is not None):
        # Get next version number
        latest_version = db.query(Version).filter(
            Version.file_id == diagram_id
        ).order_by(Version.version_number.desc()).first()
        
        next_version_number = (latest_version.version_number + 1) if latest_version else 1
        
        # Create version snapshot
        new_version = Version(
            id=str(uuid.uuid4()),
            file_id=diagram_id,
            version_number=next_version_number,
            canvas_data=diagram.canvas_data if update_data.canvas_data is not None else None,
            note_content=diagram.note_content if update_data.note_content is not None else None,
            description=version_description,
            created_by=user_id
        )
        
        db.add(new_version)
        diagram.current_version = next_version_number
        
        # Only update last_auto_versioned_at for non-major edits (so major edits don't block the 5-minute timer)
        if not is_major_edit:
            diagram.last_auto_versioned_at = datetime.utcnow()
        
        # Commit first so the version exists before generating thumbnail
        db.commit()
        
        # Generate thumbnail for the version (async call)
        if diagram.canvas_data:
            try:
                thumbnail_url = await generate_thumbnail(new_version.id, diagram.canvas_data)
                if thumbnail_url:
                    new_version.thumbnail_url = thumbnail_url
                    db.commit()
                    logger.info(
                        "Version thumbnail generated",
                        correlation_id=correlation_id,
                        version_id=new_version.id,
                        thumbnail_url=thumbnail_url
                    )
            except Exception as e:
                logger.warning(
                    "Failed to generate version thumbnail, continuing without thumbnail",
                    correlation_id=correlation_id,
                    version_id=new_version.id,
                    error=str(e)
                )
        
        logger.info(
            "Version created",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            version_number=next_version_number,
            description=version_description,
            is_major_edit=is_major_edit,
            user_id=user_id
        )
    else:
        # No version created, but we still need to commit the diagram updates
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


@app.post("/{diagram_id}/export")
async def increment_export_count(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Increment export count for a diagram."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    user_id = request.headers.get("X-User-ID")
    
    logger.info(
        "Incrementing export count",
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
    
    # Increment export count
    old_count = diagram.export_count if hasattr(diagram, 'export_count') else 0
    diagram.export_count = old_count + 1
    diagram.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Export count incremented successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        old_count=old_count,
        new_count=diagram.export_count,
        user_id=user_id
    )
    
    return {
        "message": "Export count incremented successfully",
        "id": diagram_id,
        "export_count": diagram.export_count,
        "updated_at": diagram.updated_at.isoformat()
    }


@app.get("/{diagram_id}/versions")
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
    
    # Query all versions ordered by version_number descending (newest first)
    versions = db.query(Version).filter(
        Version.file_id == diagram_id
    ).order_by(Version.version_number.desc()).all()
    
    logger.info(
        "Versions fetched successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_count=len(versions)
    )
    
    # Return versions in paginated format with metadata and size info
    enriched_versions = []
    for v in versions:
        # Calculate version size
        version_size_bytes = calculate_version_size(v)
        size_info = format_size_human_readable(version_size_bytes)
        
        enriched_versions.append({
            "id": v.id,
            "version_number": v.version_number,
            "description": v.description,
            "label": v.label,
            "thumbnail_url": v.thumbnail_url,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "created_by": v.created_by,
            "size": size_info
        })
    
    return {
        "versions": enriched_versions,
        "total": len(versions)
    }


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
        "expires_in_days": 7,            // Optional expiration
        "shared_with_email": "user@example.com"  // Share with specific user
    }
    
    Returns:
    {
        "share_id": "uuid",
        "token": "unique_token",
        "share_url": "http://localhost:3000/shared/{token}",
        "permission": "view",
        "is_public": true,
        "expires_at": "2025-12-30T00:00:00Z" or null,
        "shared_with_email": "user@example.com" or null
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
    shared_with_email = body.get("shared_with_email")
    
    # Validate permission
    if permission not in ["view", "edit"]:
        raise HTTPException(status_code=400, detail="Permission must be 'view' or 'edit'")
    
    # If sharing with specific user, look up user by email
    shared_with_user_id = None
    if shared_with_email:
        shared_user = db.query(User).filter(User.email == shared_with_email).first()
        if not shared_user:
            logger.warning(
                "Share creation failed - user not found",
                correlation_id=correlation_id,
                shared_with_email=shared_with_email
            )
            raise HTTPException(status_code=404, detail=f"User with email {shared_with_email} not found")
        shared_with_user_id = shared_user.id
        # User-specific shares are not public
        is_public = False
    
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
        shared_with_user_id=shared_with_user_id,
        expires_at=expires_at,
        view_count=0,
        created_by=user_id,
        created_at=datetime.now(tz.utc)
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    # Increment collaborator count if sharing with a specific user
    if shared_with_user_id:
        # Count unique collaborators (owner + shared users)
        unique_collaborators = db.query(Share.shared_with_user_id).filter(
            Share.file_id == diagram_id,
            Share.shared_with_user_id.isnot(None)
        ).distinct().count()
        
        # Update collaborator count (owner + shared users)
        diagram.collaborator_count = 1 + unique_collaborators
        db.commit()
    
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
        is_public=is_public,
        shared_with_email=shared_with_email
    )
    
    return {
        "share_id": share.id,
        "token": token,
        "share_url": share_url,
        "permission": permission,
        "is_public": is_public,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "has_password": password is not None,
        "shared_with_email": shared_with_email
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
    
    # Store shared_with_user_id before deletion
    shared_with_user_id = share.shared_with_user_id
    
    # Delete the share
    db.delete(share)
    db.commit()
    
    # Decrement collaborator count if this was a user-specific share
    if shared_with_user_id:
        # Count remaining unique collaborators (owner + shared users)
        unique_collaborators = db.query(Share.shared_with_user_id).filter(
            Share.file_id == diagram_id,
            Share.shared_with_user_id.isnot(None)
        ).distinct().count()
        
        # Update collaborator count (owner + shared users)
        diagram.collaborator_count = 1 + unique_collaborators
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


# ==========================================
# COMMENTS API ENDPOINTS (Full Implementation)
# ==========================================

class CreateCommentRequest(BaseModel):
    """Request model for creating a comment."""
    content: str
    parent_id: Optional[str] = None  # For threaded replies
    position_x: Optional[float] = None  # For canvas comments
    position_y: Optional[float] = None
    element_id: Optional[str] = None  # TLDraw element ID
    is_private: Optional[bool] = False  # Private comments visible only to team

class UpdateCommentRequest(BaseModel):
    """Request model for updating a comment."""
    content: str

class CommentResponse(BaseModel):
    """Response model for a comment."""
    id: str
    file_id: str
    user_id: str
    parent_id: Optional[str] = None
    content: str
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    element_id: Optional[str] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    is_private: bool = False
    created_at: datetime
    updated_at: datetime
    user: Optional[Dict[str, Any]] = None  # User info
    replies_count: int = 0
    reactions: Optional[Dict[str, int]] = None  # Emoji -> count
    mentions: Optional[list[str]] = None  # User IDs mentioned
    permalink: Optional[str] = None  # Direct link to comment

    class Config:
        from_attributes = True


@app.get("/{diagram_id}/comments")
async def get_comments(
    diagram_id: str,
    request: Request,
    is_resolved: Optional[bool] = None,
    parent_id: Optional[str] = None,
    sort_by: Optional[str] = "oldest",  # oldest, newest, most_reactions
    db: Session = Depends(get_db)
):
    """Get all comments for a diagram with filters and sorting."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Getting comments for diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Verify diagram exists and user has access
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Build query
    query = db.query(Comment).filter(Comment.file_id == diagram_id)
    
    # Apply filters
    if is_resolved is not None:
        query = query.filter(Comment.is_resolved == is_resolved)
    
    if parent_id is not None:
        query = query.filter(Comment.parent_id == parent_id)
    
    # Apply sorting
    if sort_by == "newest":
        comments = query.order_by(Comment.created_at.desc()).all()
    elif sort_by == "most_reactions":
        # For most_reactions, we need to fetch all and sort in memory
        comments = query.all()
    else:  # oldest (default)
        comments = query.order_by(Comment.created_at.asc()).all()
    
    # Enrich comments with user info and reactions
    enriched_comments = []
    for comment in comments:
        # Get user info
        user = db.query(User).filter(User.id == comment.user_id).first()
        
        # Count replies
        replies_count = db.query(Comment).filter(Comment.parent_id == comment.id).count()
        
        # Get reactions grouped by emoji
        reactions_query = db.query(
            CommentReaction.emoji,
            func.count(CommentReaction.id).label('count')
        ).filter(
            CommentReaction.comment_id == comment.id
        ).group_by(CommentReaction.emoji).all()
        
        reactions = {emoji: count for emoji, count in reactions_query}
        total_reactions = sum(reactions.values())
        
        # Get mentions
        mentions = db.query(Mention).filter(Mention.comment_id == comment.id).all()
        mentioned_user_ids = [m.user_id for m in mentions]
        
        # Generate permalink
        base_url = request.base_url
        permalink = f"{base_url}diagram/{diagram_id}#comment-{comment.id}"
        
        comment_dict = {
            "id": comment.id,
            "file_id": comment.file_id,
            "user_id": comment.user_id,
            "parent_id": comment.parent_id,
            "content": comment.content,
            "position_x": comment.position_x,
            "position_y": comment.position_y,
            "element_id": comment.element_id,
            "is_resolved": comment.is_resolved,
            "resolved_at": comment.resolved_at,
            "resolved_by": comment.resolved_by,
            "is_private": comment.is_private,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "user": {
                "id": user.id if user else None,
                "full_name": user.full_name if user else "Unknown",
                "email": user.email if user else None,
                "avatar_url": user.avatar_url if user else None
            },
            "replies_count": replies_count,
            "reactions": reactions,
            "total_reactions": total_reactions,
            "mentions": mentioned_user_ids,
            "permalink": permalink
        }
        
        enriched_comments.append(comment_dict)
    
    # Sort by most_reactions if requested
    if sort_by == "most_reactions":
        enriched_comments.sort(key=lambda x: x["total_reactions"], reverse=True)
    
    logger.info(
        "Comments retrieved successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        count=len(enriched_comments)
    )
    
    return {
        "comments": enriched_comments,
        "total": len(enriched_comments)
    }


@app.post("/{diagram_id}/comments", status_code=201)
async def create_comment(
    diagram_id: str,
    request: Request,
    comment_data: CreateCommentRequest,
    db: Session = Depends(get_db)
):
    """Create a new comment on a diagram."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Creating comment on diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Verify diagram exists
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Create comment
    new_comment = Comment(
        id=str(uuid.uuid4()),
        file_id=diagram_id,
        user_id=user_id,
        parent_id=comment_data.parent_id,
        content=comment_data.content,
        position_x=comment_data.position_x,
        position_y=comment_data.position_y,
        element_id=comment_data.element_id,
        is_private=comment_data.is_private or False
    )
    
    db.add(new_comment)
    
    # Increment comment count on diagram
    diagram.comment_count = (diagram.comment_count or 0) + 1
    diagram.last_activity = datetime.utcnow()
    diagram.updated_at = datetime.utcnow()
    
    # Extract and create mentions
    import re
    mention_pattern = r'@(\w+)'
    mentioned_usernames = re.findall(mention_pattern, comment_data.content)
    
    for username in mentioned_usernames:
        # Find user by email (assuming username is email prefix)
        mentioned_user = db.query(User).filter(
            User.email.like(f"{username}%")
        ).first()
        
        if mentioned_user:
            mention = Mention(
                id=str(uuid.uuid4()),
                comment_id=new_comment.id,
                user_id=mentioned_user.id
            )
            db.add(mention)
    
    db.commit()
    db.refresh(new_comment)
    
    # Get user info for response
    user = db.query(User).filter(User.id == user_id).first()
    
    logger.info(
        "Comment created successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        comment_id=new_comment.id,
        mentions_count=len(mentioned_usernames)
    )
    
    # Send WebSocket notification
    collaboration_service_url = os.getenv("COLLABORATION_SERVICE_URL", "http://localhost:8083")
    room_id = f"file:{diagram_id}"
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{collaboration_service_url}/broadcast/{room_id}",
                json={
                    "type": "comment_added",
                    "comment_id": new_comment.id,
                    "diagram_id": diagram_id,
                    "user_id": user_id,
                    "content": comment_data.content[:100],  # Truncate for notification
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        logger.warning(
            "Failed to send WebSocket notification for comment",
            correlation_id=correlation_id,
            error=str(e)
        )
    
    # Generate permalink
    base_url = str(request.base_url)
    permalink = f"{base_url}diagram/{diagram_id}#comment-{new_comment.id}"
    
    return {
        "id": new_comment.id,
        "file_id": new_comment.file_id,
        "user_id": new_comment.user_id,
        "parent_id": new_comment.parent_id,
        "content": new_comment.content,
        "position_x": new_comment.position_x,
        "position_y": new_comment.position_y,
        "element_id": new_comment.element_id,
        "is_resolved": new_comment.is_resolved,
        "is_private": new_comment.is_private,
        "created_at": new_comment.created_at.isoformat(),
        "updated_at": new_comment.updated_at.isoformat(),
        "permalink": permalink,
        "user": {
            "id": user.id if user else None,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None,
            "avatar_url": user.avatar_url if user else None
        },
        "replies_count": 0,
        "reactions": {},
        "mentions": mentioned_usernames
    }


@app.put("/{diagram_id}/comments/{comment_id}")
async def update_comment(
    diagram_id: str,
    comment_id: str,
    request: Request,
    comment_data: UpdateCommentRequest,
    db: Session = Depends(get_db)
):
    """Update a comment (edit within 5 minutes)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Updating comment",
        correlation_id=correlation_id,
        comment_id=comment_id,
        user_id=user_id
    )
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.file_id == diagram_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership
    if comment.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    # Check if within 5 minutes
    time_since_creation = (datetime.utcnow() - comment.created_at.replace(tzinfo=None)).total_seconds()
    if time_since_creation > 300:  # 5 minutes
        raise HTTPException(status_code=403, detail="Comments can only be edited within 5 minutes of creation")
    
    # Update comment
    comment.content = comment_data.content
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    logger.info(
        "Comment updated successfully",
        correlation_id=correlation_id,
        comment_id=comment_id
    )
    
    return {
        "id": comment.id,
        "content": comment.content,
        "updated_at": comment.updated_at.isoformat(),
        "message": "Comment updated successfully"
    }


@app.delete("/{diagram_id}/comments/{comment_id}/delete")
async def delete_comment_permanently(
    diagram_id: str,
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a comment permanently."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Deleting comment permanently",
        correlation_id=correlation_id,
        comment_id=comment_id,
        user_id=user_id
    )
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.file_id == diagram_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check ownership or admin
    diagram = db.query(File).filter(File.id == diagram_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    
    is_owner = comment.user_id == user_id
    is_diagram_owner = diagram and diagram.owner_id == user_id
    is_admin = user and user.role == "admin"
    
    if not (is_owner or is_diagram_owner or is_admin):
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    # Delete comment (cascades to mentions and reactions)
    db.delete(comment)
    
    # Decrement comment count
    if diagram:
        diagram.comment_count = max(0, (diagram.comment_count or 1) - 1)
        diagram.updated_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(
        "Comment deleted permanently",
        correlation_id=correlation_id,
        comment_id=comment_id
    )
    
    return {
        "message": "Comment deleted successfully",
        "comment_id": comment_id
    }


@app.post("/{diagram_id}/comments/{comment_id}/resolve")
async def resolve_comment(
    diagram_id: str,
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Mark a comment as resolved."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.file_id == diagram_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Mark as resolved
    comment.is_resolved = True
    comment.resolved_at = datetime.utcnow()
    comment.resolved_by = user_id
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    logger.info(
        "Comment resolved",
        correlation_id=correlation_id,
        comment_id=comment_id,
        resolved_by=user_id
    )
    
    return {
        "message": "Comment resolved",
        "comment_id": comment_id,
        "is_resolved": True,
        "resolved_at": comment.resolved_at.isoformat()
    }


@app.post("/{diagram_id}/comments/{comment_id}/reopen")
async def reopen_comment(
    diagram_id: str,
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Reopen a resolved comment."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.file_id == diagram_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Reopen comment
    comment.is_resolved = False
    comment.resolved_at = None
    comment.resolved_by = None
    comment.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(comment)
    
    logger.info(
        "Comment reopened",
        correlation_id=correlation_id,
        comment_id=comment_id,
        reopened_by=user_id
    )
    
    return {
        "message": "Comment reopened",
        "comment_id": comment_id,
        "is_resolved": False
    }


@app.post("/{diagram_id}/comments/{comment_id}/reactions")
async def add_reaction(
    diagram_id: str,
    comment_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Add an emoji reaction to a comment."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Parse request body for emoji
    body = await request.json()
    emoji = body.get("emoji")
    
    if not emoji:
        raise HTTPException(status_code=400, detail="Emoji is required")
    
    # Verify comment exists
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.file_id == diagram_id
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if reaction already exists (unique constraint)
    existing_reaction = db.query(CommentReaction).filter(
        CommentReaction.comment_id == comment_id,
        CommentReaction.user_id == user_id,
        CommentReaction.emoji == emoji
    ).first()
    
    if existing_reaction:
        # Remove reaction (toggle)
        db.delete(existing_reaction)
        db.commit()
        
        logger.info(
            "Reaction removed",
            correlation_id=correlation_id,
            comment_id=comment_id,
            emoji=emoji,
            user_id=user_id
        )
        
        return {
            "message": "Reaction removed",
            "emoji": emoji,
            "action": "removed"
        }
    else:
        # Add reaction
        reaction = CommentReaction(
            id=str(uuid.uuid4()),
            comment_id=comment_id,
            user_id=user_id,
            emoji=emoji
        )
        
        db.add(reaction)
        db.commit()
        
        logger.info(
            "Reaction added",
            correlation_id=correlation_id,
            comment_id=comment_id,
            emoji=emoji,
            user_id=user_id
        )
        
        return {
            "message": "Reaction added",
            "emoji": emoji,
            "action": "added"
        }


# ==========================================
# VERSION HISTORY API ENDPOINTS
# ==========================================

class CreateVersionRequest(BaseModel):
    """Request model for creating a version snapshot."""
    description: Optional[str] = None
    label: Optional[str] = None

class UpdateVersionLabelRequest(BaseModel):
    """Request model for updating a version label."""
    label: Optional[str] = None

class UpdateVersionDescriptionRequest(BaseModel):
    """Request model for updating a version description/comment."""
    description: Optional[str] = None

class UpdateVersionContentRequest(BaseModel):
    """Request model for updating version content (ALWAYS REJECTED - versions are immutable)."""
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None

class VersionResponse(BaseModel):
    """Response model for a version."""
    id: str
    file_id: str
    version_number: int
    canvas_data: Optional[Dict[str, Any]] = None
    note_content: Optional[str] = None
    description: Optional[str] = None
    label: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_by: str
    created_at: datetime
    user: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


@app.post("/{diagram_id}/versions", status_code=201)
async def create_version(
    diagram_id: str,
    request: Request,
    version_data: CreateVersionRequest,
    db: Session = Depends(get_db)
):
    """Create a manual version snapshot."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Creating version snapshot",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id
    )
    
    # Verify diagram exists
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Get next version number
    latest_version = db.query(Version).filter(
        Version.file_id == diagram_id
    ).order_by(Version.version_number.desc()).first()
    
    next_version_number = (latest_version.version_number + 1) if latest_version else 1
    
    # Create version snapshot
    new_version = Version(
        id=str(uuid.uuid4()),
        file_id=diagram_id,
        version_number=next_version_number,
        canvas_data=diagram.canvas_data,
        note_content=diagram.note_content,
        description=version_data.description,
        label=version_data.label,
        created_by=user_id
    )
    
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    
    # Generate thumbnail for the version (async call)
    if diagram.canvas_data:
        try:
            thumbnail_url = await generate_thumbnail(new_version.id, diagram.canvas_data)
            if thumbnail_url:
                new_version.thumbnail_url = thumbnail_url
                db.commit()
                db.refresh(new_version)
                logger.info(
                    "Version thumbnail generated",
                    correlation_id=correlation_id,
                    version_id=new_version.id,
                    thumbnail_url=thumbnail_url
                )
        except Exception as e:
            logger.warning(
                "Failed to generate version thumbnail, continuing without thumbnail",
                correlation_id=correlation_id,
                version_id=new_version.id,
                error=str(e)
            )
    
    # Get user info
    user = db.query(User).filter(User.id == user_id).first()
    
    logger.info(
        "Version snapshot created",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=new_version.id,
        version_number=next_version_number
    )
    
    return {
        "id": new_version.id,
        "file_id": new_version.file_id,
        "version_number": new_version.version_number,
        "description": new_version.description,
        "label": new_version.label,
        "thumbnail_url": new_version.thumbnail_url,
        "created_by": new_version.created_by,
        "created_at": new_version.created_at.isoformat(),
        "user": {
            "id": user.id if user else None,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None
        }
    }


@app.get("/{diagram_id}/versions")
async def get_versions(
    diagram_id: str,
    request: Request,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    search: Optional[str] = None,
    author: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all versions for a diagram with optional search/filter."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Getting versions for diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        user_id=user_id,
        search=search,
        author=author,
        date_from=date_from,
        date_to=date_to
    )
    
    # Verify diagram exists
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Build query with filters
    query = db.query(Version).filter(Version.file_id == diagram_id)
    
    # Search by content (in description, label, canvas_data, note_content)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Version.description.ilike(search_term),
                Version.label.ilike(search_term),
                cast(Version.canvas_data, String).ilike(search_term),
                Version.note_content.ilike(search_term)
            )
        )
    
    # Filter by author (by user ID or name/email)
    if author:
        # Try to find user by name or email
        author_search = f"%{author}%"
        matching_users = db.query(User).filter(
            or_(
                User.full_name.ilike(author_search),
                User.email.ilike(author_search),
                User.id == author
            )
        ).all()
        
        if matching_users:
            user_ids = [u.id for u in matching_users]
            query = query.filter(Version.created_by.in_(user_ids))
        else:
            # No matching users, return empty result
            return {
                "versions": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
    
    # Filter by date range
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Version.created_at >= from_date)
        except ValueError:
            pass  # Ignore invalid dates
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            # Add one day to include the entire date_to
            to_date = to_date + timedelta(days=1)
            query = query.filter(Version.created_at < to_date)
        except ValueError:
            pass  # Ignore invalid dates
    
    total = query.count()
    
    versions = query.order_by(
        Version.version_number.desc()
    ).offset(offset).limit(limit).all()
    
    # Enrich versions with user info and size
    enriched_versions = []
    for version in versions:
        user = db.query(User).filter(User.id == version.created_by).first()
        
        # Calculate version size
        version_size_bytes = calculate_version_size(version)
        size_info = format_size_human_readable(version_size_bytes)
        
        version_dict = {
            "id": version.id,
            "file_id": version.file_id,
            "version_number": version.version_number,
            "description": version.description,
            "label": version.label,
            "thumbnail_url": version.thumbnail_url,
            "created_by": version.created_by,
            "created_at": version.created_at.isoformat(),
            "size": size_info,  # Add size information
            "user": {
                "id": user.id if user else None,
                "full_name": user.full_name if user else "Unknown",
                "email": user.email if user else None
            }
        }
        
        enriched_versions.append(version_dict)
    
    logger.info(
        "Versions retrieved successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        count=len(enriched_versions),
        total=total
    )
    
    return {
        "versions": enriched_versions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/{diagram_id}/versions/compare")
async def compare_versions(
    diagram_id: str,
    v1: int,
    v2: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Compare two versions and return differences.
    
    Args:
        diagram_id: The diagram ID
        v1: First version number
        v2: Second version number
    
    Returns:
        Comparison data with additions, deletions, and modifications
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Comparing versions",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        v1=v1,
        v2=v2,
        user_id=user_id
    )
    
    # Get both versions
    version1 = db.query(Version).filter(
        Version.file_id == diagram_id,
        Version.version_number == v1
    ).first()
    
    version2 = db.query(Version).filter(
        Version.file_id == diagram_id,
        Version.version_number == v2
    ).first()
    
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    # Get canvas data (decompress if necessary)
    canvas1, _ = get_version_content(version1)
    canvas2, _ = get_version_content(version2)
    
    canvas1 = canvas1 or {}
    canvas2 = canvas2 or {}
    
    # Extract elements from canvas data
    # Try different common keys for elements (shapes, elements, objects, etc.)
    elements1 = {}
    elements2 = {}
    
    # Get elements from canvas1
    if isinstance(canvas1, dict):
        if 'shapes' in canvas1:
            elements1 = {str(s.get('id', i)): s for i, s in enumerate(canvas1.get('shapes', []))}
        elif 'elements' in canvas1:
            elements1 = {str(e.get('id', i)): e for i, e in enumerate(canvas1.get('elements', []))}
        elif 'objects' in canvas1:
            elements1 = {str(o.get('id', i)): o for i, o in enumerate(canvas1.get('objects', []))}
    
    # Get elements from canvas2
    if isinstance(canvas2, dict):
        if 'shapes' in canvas2:
            elements2 = {str(s.get('id', i)): s for i, s in enumerate(canvas2.get('shapes', []))}
        elif 'elements' in canvas2:
            elements2 = {str(e.get('id', i)): e for i, e in enumerate(canvas2.get('elements', []))}
        elif 'objects' in canvas2:
            elements2 = {str(o.get('id', i)): o for i, o in enumerate(canvas2.get('objects', []))}
    
    # Calculate differences
    ids1 = set(elements1.keys())
    ids2 = set(elements2.keys())
    
    # Additions: in v2 but not in v1
    added_ids = ids2 - ids1
    additions = [elements2[id] for id in added_ids]
    
    # Deletions: in v1 but not in v2
    deleted_ids = ids1 - ids2
    deletions = [elements1[id] for id in deleted_ids]
    
    # Modifications: in both but different
    common_ids = ids1 & ids2
    modifications = []
    for id in common_ids:
        elem1 = elements1[id]
        elem2 = elements2[id]
        # Simple comparison - consider different if not equal
        if elem1 != elem2:
            modifications.append({
                "id": id,
                "before": elem1,
                "after": elem2,
                "changes": _detect_element_changes(elem1, elem2)
            })
    
    # Compare note content
    note1 = version1.note_content or ""
    note2 = version2.note_content or ""
    note_changed = note1 != note2
    
    # Get user info for both versions
    user1 = db.query(User).filter(User.id == version1.created_by).first()
    user2 = db.query(User).filter(User.id == version2.created_by).first()
    
    logger.info(
        "Version comparison completed",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        additions=len(additions),
        deletions=len(deletions),
        modifications=len(modifications),
        note_changed=note_changed
    )
    
    return {
        "diagram_id": diagram_id,
        "version1": {
            "id": version1.id,
            "version_number": version1.version_number,
            "description": version1.description,
            "label": version1.label,
            "thumbnail_url": version1.thumbnail_url,
            "created_by": version1.created_by,
            "created_at": version1.created_at.isoformat(),
            "user": {
                "id": user1.id if user1 else None,
                "full_name": user1.full_name if user1 else "Unknown"
            },
            "canvas_data": canvas1,
            "note_content": note1
        },
        "version2": {
            "id": version2.id,
            "version_number": version2.version_number,
            "description": version2.description,
            "label": version2.label,
            "thumbnail_url": version2.thumbnail_url,
            "created_by": version2.created_by,
            "created_at": version2.created_at.isoformat(),
            "user": {
                "id": user2.id if user2 else None,
                "full_name": user2.full_name if user2 else "Unknown"
            },
            "canvas_data": canvas2,
            "note_content": note2
        },
        "differences": {
            "additions": additions,
            "deletions": deletions,
            "modifications": modifications,
            "note_changed": note_changed,
            "summary": {
                "total_changes": len(additions) + len(deletions) + len(modifications),
                "added_count": len(additions),
                "deleted_count": len(deletions),
                "modified_count": len(modifications)
            }
        }
    }


def _detect_element_changes(elem1: dict, elem2: dict) -> list:
    """Detect what changed between two elements.
    
    Returns list of change descriptions.
    """
    changes = []
    
    # Compare common properties
    for key in set(elem1.keys()) | set(elem2.keys()):
        val1 = elem1.get(key)
        val2 = elem2.get(key)
        
        if val1 != val2:
            if key not in elem1:
                changes.append(f"Added {key}: {val2}")
            elif key not in elem2:
                changes.append(f"Removed {key}: {val1}")
            else:
                # Property changed
                if key == "x" or key == "y":
                    changes.append(f"Moved")
                elif key == "width" or key == "height":
                    changes.append(f"Resized")
                elif key == "rotation":
                    changes.append(f"Rotated")
                elif key == "color" or key == "fill" or key == "stroke":
                    changes.append(f"Color changed")
                elif key == "text" or key == "label":
                    changes.append(f"Text changed")
                else:
                    changes.append(f"Changed {key}")
    
    # Deduplicate changes
    return list(set(changes))


@app.get("/{diagram_id}/versions/{version_id}")
async def get_version(
    diagram_id: str,
    version_id: str,
    request: Request,
    include_content: bool = True,
    db: Session = Depends(get_db)
):
    """Get a specific version by ID with locking information.
    
    Historical versions are always locked (read-only). Version content (canvas_data, note_content)
    cannot be modified. Only metadata (label, description) can be updated.
    
    To edit a version's content, you must restore it to the current diagram first.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Getting specific version",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram to check if this is the current version
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Determine if version is locked (all historical versions are locked)
    latest_version = db.query(Version).filter(
        Version.file_id == diagram_id
    ).order_by(Version.version_number.desc()).first()
    
    is_locked = True  # All versions are immutable snapshots
    is_latest = latest_version and version.id == latest_version.id
    
    # Get user info
    user = db.query(User).filter(User.id == version.created_by).first()
    
    # Calculate version size
    version_size_bytes = calculate_version_size(version)
    size_info = format_size_human_readable(version_size_bytes)
    
    response_data = {
        "id": version.id,
        "file_id": version.file_id,
        "version_number": version.version_number,
        "description": version.description,
        "label": version.label,
        "thumbnail_url": version.thumbnail_url,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat(),
        "is_locked": is_locked,  # Always true - versions are immutable
        "is_latest": is_latest,
        "is_read_only": True,  # Historical versions are always read-only
        "size": size_info,  # Add size information
        "user": {
            "id": user.id if user else None,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None
        },
        "message": "Historical version is read-only. To edit, restore this version first."
    }
    
    # Include full content if requested
    if include_content:
        # Use decompression helper if version is compressed
        canvas_data, note_content = get_version_content(version)
        response_data["canvas_data"] = canvas_data
        response_data["note_content"] = note_content
        response_data["is_compressed"] = version.is_compressed
        if version.is_compressed:
            response_data["compression_info"] = {
                "original_size": version.original_size,
                "compressed_size": version.compressed_size,
                "compression_ratio": version.compression_ratio,
                "savings_percent": round((1 - version.compression_ratio) * 100, 1) if version.compression_ratio else 0,
                "compressed_at": version.compressed_at.isoformat() if version.compressed_at else None
            }
    
    logger.info(
        "Version retrieved successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        version_number=version.version_number
    )
    
    return response_data


@app.patch("/{diagram_id}/versions/{version_id}/label")
async def update_version_label(
    diagram_id: str,
    version_id: str,
    request: Request,
    label_data: UpdateVersionLabelRequest,
    db: Session = Depends(get_db)
):
    """Update the label of a specific version.
    
    Note: This only updates metadata. Version content (canvas_data, note_content) is immutable.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Updating version label",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id,
        new_label=label_data.label
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Update label (metadata only - content is locked)
    version.label = label_data.label
    db.commit()
    db.refresh(version)
    
    # Get user info
    user = db.query(User).filter(User.id == version.created_by).first()
    
    logger.info(
        "Version label updated successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        version_number=version.version_number,
        label=version.label
    )
    
    return {
        "id": version.id,
        "file_id": version.file_id,
        "version_number": version.version_number,
        "description": version.description,
        "label": version.label,
        "thumbnail_url": version.thumbnail_url,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat(),
        "user": {
            "id": user.id if user else None,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None
        }
    }


@app.patch("/{diagram_id}/versions/{version_id}/description")
async def update_version_description(
    diagram_id: str,
    version_id: str,
    request: Request,
    description_data: UpdateVersionDescriptionRequest,
    db: Session = Depends(get_db)
):
    """Update the description/comment of a specific version.
    
    Note: This only updates metadata. Version content (canvas_data, note_content) is immutable.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Updating version description",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Update description (metadata only - content is locked)
    version.description = description_data.description
    db.commit()
    db.refresh(version)
    
    # Get user info
    user = db.query(User).filter(User.id == version.created_by).first()
    
    logger.info(
        "Version description updated successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        version_number=version.version_number
    )
    
    return {
        "id": version.id,
        "file_id": version.file_id,
        "version_number": version.version_number,
        "description": version.description,
        "label": version.label,
        "thumbnail_url": version.thumbnail_url,
        "created_by": version.created_by,
        "created_at": version.created_at.isoformat(),
        "user": {
            "id": user.id if user else None,
            "full_name": user.full_name if user else "Unknown",
            "email": user.email if user else None
        }
    }


@app.patch("/{diagram_id}/versions/{version_id}/content")
async def update_version_content(
    diagram_id: str,
    version_id: str,
    request: Request,
    content_data: UpdateVersionContentRequest,
    db: Session = Depends(get_db)
):
    """Attempt to update version content (ALWAYS REJECTED).
    
    Historical versions are immutable. Their content (canvas_data, note_content) cannot be modified.
    This endpoint exists to explicitly document this behavior and provide a clear error message.
    
    To edit a version's content:
    1. Use POST /{diagram_id}/versions/{version_id}/restore to restore the version
    2. Then edit the current diagram using PUT /{diagram_id}
    
    Only version metadata (label, description) can be updated via:
    - PATCH /{diagram_id}/versions/{version_id}/label
    - PATCH /{diagram_id}/versions/{version_id}/description
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    logger.warning(
        "Attempt to modify locked version content (rejected)",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version to provide informative error
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Always reject content modification
    raise HTTPException(
        status_code=403,
        detail={
            "error": "Version content is locked",
            "message": "Historical versions are read-only. Version content (canvas_data, note_content) cannot be modified.",
            "version_number": version.version_number,
            "is_locked": True,
            "alternatives": {
                "restore_then_edit": f"POST /{diagram_id}/versions/{version_id}/restore then PUT /{diagram_id}",
                "update_label": f"PATCH /{diagram_id}/versions/{version_id}/label",
                "update_description": f"PATCH /{diagram_id}/versions/{version_id}/description"
            }
        }
    )


@app.post("/{diagram_id}/versions/{version_id}/share")
async def create_version_share_link(
    diagram_id: str,
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a public share link for a specific version of a diagram.
    
    Request body (optional):
    {
        "permission": "view",  // Only view supported for versions (read-only)
        "expires_in_days": 7   // Optional expiration
    }
    
    Returns:
    {
        "share_id": "uuid",
        "token": "unique_token",
        "share_url": "http://localhost:3000/version-shared/{token}",
        "version_number": 5,
        "expires_at": "2025-12-30T00:00:00Z" or null
    }
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        logger.warning(
            "Unauthorized version share creation attempt - no user ID",
            correlation_id=correlation_id,
            diagram_id=diagram_id,
            version_id=version_id
        )
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Creating version share link",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        logger.warning(
            "Version share creation failed - version not found",
            correlation_id=correlation_id,
            version_id=version_id
        )
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram to check ownership
    diagram = db.query(File).filter(
        File.id == diagram_id,
        File.is_deleted == False
    ).first()
    
    if not diagram:
        logger.warning(
            "Version share creation failed - diagram not found",
            correlation_id=correlation_id,
            diagram_id=diagram_id
        )
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check authorization (only owner can share)
    if diagram.owner_id != user_id:
        logger.warning(
            "Unauthorized version share creation attempt",
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
    
    expires_in_days = body.get("expires_in_days")
    
    # Version shares are always read-only
    permission = "view"
    
    # Generate unique share token
    import secrets
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = None
    if expires_in_days:
        from datetime import timedelta, timezone as tz
        expires_at = datetime.now(tz.utc) + timedelta(days=expires_in_days)
    
    # Create share record for this specific version
    share = Share(
        id=str(uuid.uuid4()),
        file_id=diagram_id,
        version_id=version_id,  # This makes it a version-specific share
        token=token,
        permission=permission,
        is_public=True,
        expires_at=expires_at,
        view_count=0,
        created_by=user_id,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    # Build share URL (different from regular share)
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    share_url = f"{frontend_url}/version-shared/{token}"
    
    logger.info(
        "Version share link created successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        version_number=version.version_number,
        share_id=share.id,
        token=token[:10] + "..."
    )
    
    return {
        "share_id": share.id,
        "token": token,
        "share_url": share_url,
        "version_number": version.version_number,
        "permission": permission,
        "expires_at": expires_at.isoformat() if expires_at else None
    }

@app.get("/version-shared/{token}")
async def get_shared_version(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Access a shared version via its public token.
    
    Returns:
    {
        "id": "diagram_id",
        "title": "Diagram Title",
        "type": "canvas",
        "version_number": 5,
        "version_label": "Production Release",
        "version_description": "Fixed authentication bug",
        "canvas_data": {...},
        "note_content": "...",
        "created_at": "2025-12-24T00:00:00Z",
        "permission": "view",
        "is_read_only": true
    }
    """
    logger.info("Accessing shared version", token=token[:10] + "...")
    
    # Find share by token
    share = db.query(Share).filter(
        Share.token == token,
        Share.version_id.isnot(None)  # Must be a version share
    ).first()
    
    if not share:
        logger.warning("Shared version access failed - invalid token", token=token[:10] + "...")
        raise HTTPException(status_code=404, detail="Invalid or expired share link")
    
    # Check expiration
    if share.expires_at:
        if datetime.now(timezone.utc) > share.expires_at:
            logger.warning("Shared version access failed - link expired", token=token[:10] + "...")
            raise HTTPException(status_code=403, detail="This share link has expired")
    
    # Get version
    version = db.query(Version).filter(
        Version.id == share.version_id
    ).first()
    
    if not version:
        logger.warning("Shared version access failed - version not found", version_id=share.version_id)
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram info
    diagram = db.query(File).filter(File.id == share.file_id).first()
    
    if not diagram:
        logger.warning("Shared version access failed - diagram not found", diagram_id=share.file_id)
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Update analytics
    share.view_count += 1
    share.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(
        "Shared version accessed successfully",
        token=token[:10] + "...",
        diagram_id=diagram.id,
        version_id=version.id,
        version_number=version.version_number,
        view_count=share.view_count
    )
    
    # Return version data (read-only)
    return {
        "id": diagram.id,
        "title": diagram.title,
        "type": diagram.file_type,
        "version_number": version.version_number,
        "version_label": version.label,
        "version_description": version.description,
        "canvas_data": version.canvas_data,
        "note_content": version.note_content,
        "created_at": version.created_at.isoformat(),
        "permission": "view",
        "is_read_only": True  # Versions are always read-only
    }

@app.post("/{diagram_id}/versions/{version_id}/restore")
async def restore_version(
    diagram_id: str,
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Restore diagram to a previous version."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Restoring version",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Create a version of current state before restoring
    latest_version = db.query(Version).filter(
        Version.file_id == diagram_id
    ).order_by(Version.version_number.desc()).first()
    
    next_version_number = (latest_version.version_number + 1) if latest_version else 1
    
    backup_version = Version(
        id=str(uuid.uuid4()),
        file_id=diagram_id,
        version_number=next_version_number,
        canvas_data=diagram.canvas_data,
        note_content=diagram.note_content,
        description=f"Auto-backup before restore to v{version.version_number}",
        created_by=user_id
    )
    
    db.add(backup_version)
    
    # Restore the version content to diagram
    diagram.canvas_data = version.canvas_data
    diagram.note_content = version.note_content
    diagram.updated_at = datetime.utcnow()
    diagram.last_activity = datetime.utcnow()
    
    db.commit()
    db.refresh(diagram)
    
    logger.info(
        "Version restored successfully",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        restored_version_number=version.version_number,
        backup_version_number=next_version_number
    )
    
    # Send WebSocket notification
    collaboration_service_url = os.getenv("COLLABORATION_SERVICE_URL", "http://localhost:8083")
    room_id = f"file:{diagram_id}"
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                f"{collaboration_service_url}/broadcast/{room_id}",
                json={
                    "type": "version_restored",
                    "diagram_id": diagram_id,
                    "version_id": version_id,
                    "version_number": version.version_number,
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    except Exception as e:
        logger.warning(
            "Failed to send WebSocket notification for version restore",
            correlation_id=correlation_id,
            error=str(e)
        )
    
    return {
        "message": "Version restored successfully",
        "diagram_id": diagram_id,
        "restored_version": version.version_number,
        "backup_version": next_version_number,
        "updated_at": diagram.updated_at.isoformat()
    }


@app.post("/{diagram_id}/versions/{version_id}/fork")
async def fork_version(
    diagram_id: str,
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new diagram from a specific version."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Forking version to new diagram",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get original diagram for metadata
    original_diagram = db.query(File).filter(File.id == diagram_id).first()
    if not original_diagram:
        raise HTTPException(status_code=404, detail="Original diagram not found")
    
    # Create new diagram from version
    new_diagram = File(
        id=str(uuid.uuid4()),
        title=f"{original_diagram.title} (Fork from v{version.version_number})",
        file_type=original_diagram.file_type,
        canvas_data=version.canvas_data,
        note_content=version.note_content,
        owner_id=user_id,
        team_id=original_diagram.team_id,
        folder_id=original_diagram.folder_id
    )
    
    db.add(new_diagram)
    db.commit()
    db.refresh(new_diagram)
    
    # Create initial version for the forked diagram
    initial_version = Version(
        id=str(uuid.uuid4()),
        file_id=new_diagram.id,
        version_number=1,
        canvas_data=version.canvas_data,
        note_content=version.note_content,
        description=f"Forked from {original_diagram.title} v{version.version_number}",
        created_by=user_id
    )
    
    db.add(initial_version)
    db.commit()
    
    logger.info(
        "Version forked to new diagram",
        correlation_id=correlation_id,
        original_diagram_id=diagram_id,
        new_diagram_id=new_diagram.id,
        version_number=version.version_number
    )
    
    return {
        "message": "Version forked successfully",
        "original_diagram_id": diagram_id,
        "new_diagram_id": new_diagram.id,
        "new_diagram_title": new_diagram.title,
        "forked_from_version": version.version_number
    }


# ==========================================
# EXPORT ENDPOINTS
# ==========================================

@app.post("/{diagram_id}/export/png")
async def export_diagram_png(
    diagram_id: str,
    request: Request,
    scale: int = 2,  # 1x, 2x, 4x
    background: str = "white",  # white, transparent
    quality: str = "high",  # low, medium, high, ultra
    db: Session = Depends(get_db)
):
    """Export diagram as PNG."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting diagram as PNG",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        scale=scale,
        background=background
    )
    
    # Get diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Call export service
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/png",
                json={
                    "diagram_id": diagram_id,
                    "canvas_data": diagram.canvas_data or {},
                    "format": "png",
                    "scale": scale,
                    "background": background,
                    "quality": quality
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "PNG export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id
                )
                return Response(
                    content=response.content,
                    media_type="image/png",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}.png"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/{diagram_id}/export/svg")
async def export_diagram_svg(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Export diagram as SVG."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting diagram as SVG",
        correlation_id=correlation_id,
        diagram_id=diagram_id
    )
    
    # Get diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Call export service
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/svg",
                json={
                    "diagram_id": diagram_id,
                    "canvas_data": diagram.canvas_data or {},
                    "format": "svg"
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "SVG export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id
                )
                return Response(
                    content=response.content,
                    media_type="image/svg+xml",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}.svg"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/{diagram_id}/export/pdf")
async def export_diagram_pdf(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Export diagram as PDF."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting diagram as PDF",
        correlation_id=correlation_id,
        diagram_id=diagram_id
    )
    
    # Get diagram
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Call export service
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/pdf",
                json={
                    "diagram_id": diagram_id,
                    "canvas_data": diagram.canvas_data or {},
                    "format": "pdf"
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "PDF export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id
                )
                return Response(
                    content=response.content,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}.pdf"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/{diagram_id}/versions/{version_id}/export/png")
async def export_version_png(
    diagram_id: str,
    version_id: str,
    request: Request,
    scale: int = 2,  # 1x, 2x, 4x
    background: str = "white",  # white, transparent
    quality: str = "high",  # low, medium, high, ultra
    db: Session = Depends(get_db)
):
    """Export specific version as PNG.
    
    Allows exporting historical versions of a diagram, not just the current version.
    The exported PNG will reflect the canvas_data from the specified version.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting version as PNG",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id,
        scale=scale,
        background=background
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram to check permissions and increment export count
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count on the diagram
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Get version content (handles compressed versions)
    canvas_data, note_content = get_version_content(version)
    
    # Call export service with version data
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/png",
                json={
                    "diagram_id": diagram_id,
                    "version_id": version_id,
                    "version_number": version.version_number,
                    "canvas_data": canvas_data or {},
                    "format": "png",
                    "scale": scale,
                    "background": background,
                    "quality": quality
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "Version PNG export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id,
                    version_id=version_id,
                    version_number=version.version_number
                )
                return Response(
                    content=response.content,
                    media_type="image/png",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}_v{version.version_number}.png"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Version export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/{diagram_id}/versions/{version_id}/export/svg")
async def export_version_svg(
    diagram_id: str,
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Export specific version as SVG."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting version as SVG",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram to increment export count
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Get version content
    canvas_data, note_content = get_version_content(version)
    
    # Call export service
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/svg",
                json={
                    "diagram_id": diagram_id,
                    "version_id": version_id,
                    "version_number": version.version_number,
                    "canvas_data": canvas_data or {},
                    "format": "svg"
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "Version SVG export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id,
                    version_id=version_id,
                    version_number=version.version_number
                )
                return Response(
                    content=response.content,
                    media_type="image/svg+xml",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}_v{version.version_number}.svg"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Version export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/{diagram_id}/versions/{version_id}/export/pdf")
async def export_version_pdf(
    diagram_id: str,
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Export specific version as PDF."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    logger.info(
        "Exporting version as PDF",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        version_id=version_id
    )
    
    # Get version
    version = db.query(Version).filter(
        Version.id == version_id,
        Version.file_id == diagram_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Get diagram to increment export count
    diagram = db.query(File).filter(File.id == diagram_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Increment export count
    diagram.export_count = (diagram.export_count or 0) + 1
    db.commit()
    
    # Get version content
    canvas_data, note_content = get_version_content(version)
    
    # Call export service
    export_service_url = os.getenv("EXPORT_SERVICE_URL", "http://localhost:8097")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{export_service_url}/export/pdf",
                json={
                    "diagram_id": diagram_id,
                    "version_id": version_id,
                    "version_number": version.version_number,
                    "canvas_data": canvas_data or {},
                    "format": "pdf"
                }
            )
            
            if response.status_code == 200:
                logger.info(
                    "Version PDF export generated",
                    correlation_id=correlation_id,
                    diagram_id=diagram_id,
                    version_id=version_id,
                    version_number=version.version_number
                )
                return Response(
                    content=response.content,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename=diagram_{diagram_id}_v{version.version_number}.pdf"
                    }
                )
            else:
                logger.error(
                    "Export service error",
                    correlation_id=correlation_id,
                    status_code=response.status_code
                )
                raise HTTPException(status_code=500, detail="Export service error")
    except httpx.TimeoutException:
        logger.error("Export service timeout", correlation_id=correlation_id)
        raise HTTPException(status_code=504, detail="Export service timeout")
    except Exception as e:
        logger.error(
            "Version export failed",
            correlation_id=correlation_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.post("/versions/compress/all")
async def compress_all_old_versions(
    request: Request,
    min_age_days: int = 30,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Background task to compress old versions across all diagrams.
    
    This is a system-level endpoint for background compression jobs.
    Compresses versions older than min_age_days (default 30 days).
    
    Args:
        min_age_days: Minimum age in days (versions older than this will be compressed)
        limit: Maximum number of versions to compress in one batch (default 100)
    
    Returns:
        Statistics about compression batch
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    logger.info(
        "Starting background compression",
        correlation_id=correlation_id,
        min_age_days=min_age_days,
        limit=limit
    )
    
    # Find old uncompressed versions
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=min_age_days)
    old_versions = db.query(Version).filter(
        Version.is_compressed == False,
        Version.created_at < cutoff_date
    ).limit(limit).all()
    
    logger.info(
        "Found old versions to compress",
        correlation_id=correlation_id,
        count=len(old_versions)
    )
    
    # Compress each version
    results = []
    total_original = 0
    total_compressed = 0
    errors = 0
    
    for version in old_versions:
        try:
            result = compress_version(version, db)
            results.append(result)
            if result["status"] == "compressed":
                total_original += result["original_size"]
                total_compressed += result["compressed_size"]
        except Exception as e:
            logger.error(
                "Failed to compress version",
                correlation_id=correlation_id,
                version_id=version.id,
                error=str(e)
            )
            errors += 1
    
    total_savings = total_original - total_compressed
    overall_ratio = total_compressed / total_original if total_original > 0 else 0.0
    
    summary = {
        "versions_found": len(old_versions),
        "versions_compressed": len([r for r in results if r["status"] == "compressed"]),
        "versions_skipped": len([r for r in results if r["status"] == "already_compressed"]),
        "errors": errors,
        "total_original_size": total_original,
        "total_compressed_size": total_compressed,
        "total_savings_bytes": total_savings,
        "total_savings_mb": round(total_savings / (1024 * 1024), 2),
        "overall_compression_ratio": round(overall_ratio, 3),
        "savings_percent": round((total_savings / total_original * 100) if total_original > 0 else 0, 1)
    }
    
    logger.info(
        "Background compression complete",
        correlation_id=correlation_id,
        versions_found=summary["versions_found"],
        versions_compressed=summary["versions_compressed"],
        total_savings_mb=summary["total_savings_mb"]
    )
    
    return summary


@app.post("/versions/compress/diagram/{diagram_id}")
async def compress_diagram_versions(
    diagram_id: str,
    request: Request,
    min_age_days: int = 30,
    db: Session = Depends(get_db)
):
    """Compress all old versions of a specific diagram.
    
    Compresses versions older than min_age_days (default 30 days).
    This is useful for manual compression of a specific diagram's history.
    
    Args:
        diagram_id: Diagram ID
        min_age_days: Minimum age in days (versions older than this will be compressed)
    
    Returns:
        Statistics about compression (how many versions compressed, total savings)
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Compressing diagram versions",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        min_age_days=min_age_days,
        user_id=user_id
    )
    
    # Verify user owns the diagram
    diagram = db.query(File).filter(File.id == diagram_id, File.owner_id == user_id).first()
    if not diagram:
        raise HTTPException(status_code=404, detail="Diagram not found or not authorized")
    
    # Find old uncompressed versions
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=min_age_days)
    old_versions = db.query(Version).filter(
        Version.file_id == diagram_id,
        Version.is_compressed == False,
        Version.created_at < cutoff_date
    ).all()
    
    # Compress each version
    results = []
    total_original = 0
    total_compressed = 0
    
    for version in old_versions:
        result = compress_version(version, db)
        results.append(result)
        if result["status"] == "compressed":
            total_original += result["original_size"]
            total_compressed += result["compressed_size"]
    
    total_savings = total_original - total_compressed
    overall_ratio = total_compressed / total_original if total_original > 0 else 0.0
    
    summary = {
        "diagram_id": diagram_id,
        "versions_compressed": len([r for r in results if r["status"] == "compressed"]),
        "versions_skipped": len([r for r in results if r["status"] == "already_compressed"]),
        "total_original_size": total_original,
        "total_compressed_size": total_compressed,
        "total_savings_bytes": total_savings,
        "total_savings_mb": round(total_savings / (1024 * 1024), 2),
        "overall_compression_ratio": round(overall_ratio, 3),
        "savings_percent": round((total_savings / total_original * 100) if total_original > 0 else 0, 1)
    }
    
    logger.info(
        "Diagram versions compressed",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        versions_compressed=summary["versions_compressed"],
        total_savings_mb=summary["total_savings_mb"]
    )
    
    return summary


@app.post("/versions/compress/{version_id}")
async def compress_specific_version(
    version_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Manually compress a specific version.
    
    This endpoint compresses a single version's canvas_data and note_content using gzip.
    Compressed data is stored as base64-encoded strings in separate columns.
    Original uncompressed data is cleared after compression to save space.
    
    Returns compression statistics including size reduction.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    logger.info(
        "Compressing specific version",
        correlation_id=correlation_id,
        version_id=version_id,
        user_id=user_id
    )
    
    # Get version
    version = db.query(Version).filter(Version.id == version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Verify user owns the diagram
    diagram = db.query(File).filter(File.id == version.file_id).first()
    if not diagram or diagram.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Compress the version
    result = compress_version(version, db)
    
    logger.info(
        "Version compressed",
        correlation_id=correlation_id,
        vid=version_id,
        status=result.get("status"),
        original_size=result.get("original_size"),
        compressed_size=result.get("compressed_size")
    )
    
    return result


@app.get("/versions/compression/stats")
async def get_compression_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get overall compression statistics.
    
    Returns statistics about version compression across the entire system:
    - Total versions
    - Compressed vs uncompressed
    - Total storage savings
    - Average compression ratio
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Count versions
    total_versions = db.query(func.count(Version.id)).scalar()
    compressed_versions = db.query(func.count(Version.id)).filter(Version.is_compressed == True).scalar()
    uncompressed_versions = total_versions - compressed_versions
    
    # Sum sizes
    compressed_stats = db.query(
        func.sum(Version.original_size).label('total_original'),
        func.sum(Version.compressed_size).label('total_compressed'),
        func.avg(Version.compression_ratio).label('avg_ratio')
    ).filter(Version.is_compressed == True).first()
    
    total_original = int(compressed_stats.total_original or 0)
    total_compressed = int(compressed_stats.total_compressed or 0)
    avg_ratio = float(compressed_stats.avg_ratio) if compressed_stats.avg_ratio else 0.0
    total_savings = total_original - total_compressed
    
    stats = {
        "total_versions": total_versions,
        "compressed_versions": compressed_versions,
        "uncompressed_versions": uncompressed_versions,
        "compression_percentage": round((compressed_versions / total_versions * 100) if total_versions > 0 else 0, 1),
        "total_original_size_bytes": total_original,
        "total_compressed_size_bytes": total_compressed,
        "total_savings_bytes": total_savings,
        "total_savings_mb": round(total_savings / (1024 * 1024), 2),
        "total_savings_gb": round(total_savings / (1024 * 1024 * 1024), 2),
        "average_compression_ratio": round(avg_ratio, 3),
        "average_savings_percent": round((1 - avg_ratio) * 100, 1) if avg_ratio > 0 else 0
    }
    
    logger.info(
        "Compression stats retrieved",
        correlation_id=correlation_id,
        total_versions=stats["total_versions"],
        compressed_versions=stats["compressed_versions"],
        total_savings_mb=stats["total_savings_mb"]
    )
    
    return stats


# ============================================================
# VERSION RETENTION POLICY ENDPOINTS
# ============================================================

class RetentionPolicyRequest(BaseModel):
    """Request model for setting retention policy."""
    policy: str  # keep_all, keep_last_n, keep_duration
    count: Optional[int] = None  # For keep_last_n
    days: Optional[int] = None  # For keep_duration


@app.get("/{diagram_id}/retention-policy")
async def get_retention_policy(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get the version retention policy for a diagram.
    
    Returns the current retention policy settings:
    - keep_all: Keep all versions (default)
    - keep_last_n: Keep only the last N versions
    - keep_duration: Keep versions for a specified number of days
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get diagram
    file = db.query(File).filter(File.id == diagram_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check ownership
    if file.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this diagram's policy")
    
    policy_info = {
        "diagram_id": diagram_id,
        "policy": file.retention_policy or "keep_all",
        "count": file.retention_count,
        "days": file.retention_days,
        "current_version_count": file.version_count
    }
    
    logger.info(
        "Retrieved retention policy",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        policy=policy_info["policy"]
    )
    
    return policy_info


@app.put("/{diagram_id}/retention-policy")
async def set_retention_policy(
    diagram_id: str,
    policy_request: RetentionPolicyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Set the version retention policy for a diagram.
    
    Policy options:
    - keep_all: Keep all versions (default)
    - keep_last_n: Keep only the last N versions (requires count parameter)
    - keep_duration: Keep versions for a specified number of days (requires days parameter)
    
    Note: This sets the policy but does not immediately prune versions.
    Use the apply endpoint to execute the policy.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate policy
    valid_policies = ["keep_all", "keep_last_n", "keep_duration"]
    if policy_request.policy not in valid_policies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy. Must be one of: {', '.join(valid_policies)}"
        )
    
    # Validate parameters
    if policy_request.policy == "keep_last_n":
        if not policy_request.count or policy_request.count < 1:
            raise HTTPException(
                status_code=400,
                detail="keep_last_n policy requires a positive count parameter"
            )
    
    if policy_request.policy == "keep_duration":
        if not policy_request.days or policy_request.days < 1:
            raise HTTPException(
                status_code=400,
                detail="keep_duration policy requires a positive days parameter"
            )
    
    # Get diagram
    file = db.query(File).filter(File.id == diagram_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check ownership
    if file.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this diagram's policy")
    
    # Update policy
    file.retention_policy = policy_request.policy
    file.retention_count = policy_request.count
    file.retention_days = policy_request.days
    
    db.commit()
    
    policy_info = {
        "diagram_id": diagram_id,
        "policy": file.retention_policy,
        "count": file.retention_count,
        "days": file.retention_days,
        "message": "Retention policy updated successfully"
    }
    
    logger.info(
        "Updated retention policy",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        policy=policy_request.policy,
        count=policy_request.count,
        days=policy_request.days
    )
    
    return policy_info


@app.post("/{diagram_id}/retention-policy/apply")
async def apply_retention_policy(
    diagram_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Apply the retention policy and prune old versions.
    
    This will delete versions according to the configured policy:
    - keep_all: No versions deleted
    - keep_last_n: Delete all but the last N versions
    - keep_duration: Delete versions older than the specified duration
    
    Returns the number of versions deleted.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Get diagram
    file = db.query(File).filter(File.id == diagram_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="Diagram not found")
    
    # Check ownership
    if file.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to apply policy")
    
    deleted_count = 0
    policy = file.retention_policy or "keep_all"
    
    if policy == "keep_all":
        # No versions to delete
        pass
    
    elif policy == "keep_last_n":
        # Keep only the last N versions
        if not file.retention_count:
            raise HTTPException(
                status_code=400,
                detail="Retention count not configured for keep_last_n policy"
            )
        
        # Get all versions ordered by version number descending
        all_versions = db.query(Version).filter(
            Version.file_id == diagram_id
        ).order_by(Version.version_number.desc()).all()
        
        # Delete versions beyond the retention count
        if len(all_versions) > file.retention_count:
            versions_to_delete = all_versions[file.retention_count:]
            for version in versions_to_delete:
                db.delete(version)
                deleted_count += 1
    
    elif policy == "keep_duration":
        # Keep versions within the duration, delete older ones
        if not file.retention_days:
            raise HTTPException(
                status_code=400,
                detail="Retention days not configured for keep_duration policy"
            )
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=file.retention_days)
        
        # Find and delete old versions
        old_versions = db.query(Version).filter(
            Version.file_id == diagram_id,
            Version.created_at < cutoff_date
        ).all()
        
        for version in old_versions:
            db.delete(version)
            deleted_count += 1
    
    # Update version count
    if deleted_count > 0:
        file.version_count = db.query(func.count(Version.id)).filter(
            Version.file_id == diagram_id
        ).scalar()
        db.commit()
    
    result = {
        "diagram_id": diagram_id,
        "policy": policy,
        "versions_deleted": deleted_count,
        "versions_remaining": file.version_count,
        "message": f"Policy applied successfully. Deleted {deleted_count} version(s)."
    }
    
    logger.info(
        "Applied retention policy",
        correlation_id=correlation_id,
        diagram_id=diagram_id,
        policy=policy,
        deleted=deleted_count,
        remaining=file.version_count
    )
    
    return result


@app.post("/retention-policy/apply-all")
async def apply_all_retention_policies(
    request: Request,
    db: Session = Depends(get_db)
):
    """Apply retention policies to all diagrams (system-wide).
    
    This is typically called by a background job/cron.
    No authentication required as it's for system maintenance.
    
    Returns statistics about policies applied and versions deleted.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    total_diagrams = 0
    total_deleted = 0
    policies_applied = {"keep_all": 0, "keep_last_n": 0, "keep_duration": 0}
    errors = []
    
    # Get all diagrams that are not deleted
    files = db.query(File).filter(File.is_deleted == False).all()
    
    for file in files:
        try:
            total_diagrams += 1
            policy = file.retention_policy or "keep_all"
            policies_applied[policy] = policies_applied.get(policy, 0) + 1
            
            deleted_count = 0
            
            if policy == "keep_all":
                # No action needed
                pass
            
            elif policy == "keep_last_n":
                if file.retention_count:
                    # Get all versions ordered by version number descending
                    all_versions = db.query(Version).filter(
                        Version.file_id == file.id
                    ).order_by(Version.version_number.desc()).all()
                    
                    # Delete versions beyond the retention count
                    if len(all_versions) > file.retention_count:
                        versions_to_delete = all_versions[file.retention_count:]
                        for version in versions_to_delete:
                            db.delete(version)
                            deleted_count += 1
            
            elif policy == "keep_duration":
                if file.retention_days:
                    cutoff_date = datetime.now(timezone.utc) - timedelta(days=file.retention_days)
                    
                    # Find and delete old versions
                    old_versions = db.query(Version).filter(
                        Version.file_id == file.id,
                        Version.created_at < cutoff_date
                    ).all()
                    
                    for version in old_versions:
                        db.delete(version)
                        deleted_count += 1
            
            # Update version count if any were deleted
            if deleted_count > 0:
                file.version_count = db.query(func.count(Version.id)).filter(
                    Version.file_id == file.id
                ).scalar()
                total_deleted += deleted_count
            
        except Exception as e:
            errors.append({
                "diagram_id": file.id,
                "error": str(e)
            })
            logger.error(
                "Error applying retention policy",
                correlation_id=correlation_id,
                diagram_id=file.id,
                error=str(e)
            )
    
    # Commit all changes
    db.commit()
    
    result = {
        "total_diagrams_processed": total_diagrams,
        "total_versions_deleted": total_deleted,
        "policies_applied": policies_applied,
        "errors": errors,
        "error_count": len(errors)
    }
    
    logger.info(
        "Applied retention policies system-wide",
        correlation_id=correlation_id,
        diagrams=total_diagrams,
        deleted=total_deleted,
        errors=len(errors)
    )
    
    return result


# ============================================================================
# EXPORT HISTORY ENDPOINTS
# ============================================================================

@app.get("/export-history/{file_id}")
async def get_file_export_history(
    file_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Get export history for a specific file.
    
    Feature #514: Export history tracking
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    try:
        logger.info(
            f"Getting export history for file {file_id}",
            correlation_id=correlation_id,
            file_id=file_id,
            limit=limit,
            offset=offset
        )
        
        # Query export history from the export_history table
        from .models import ExportHistory
        
        history = db.query(ExportHistory).filter(
            ExportHistory.file_id == file_id
        ).order_by(
            ExportHistory.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Get total count
        total_count = db.query(func.count(ExportHistory.id)).filter(
            ExportHistory.file_id == file_id
        ).scalar()
        
        # Format response
        exports = []
        for record in history:
            exports.append({
                "id": record.id,
                "file_id": record.file_id,
                "user_id": record.user_id,
                "export_format": record.export_format,
                "export_type": record.export_type,
                "export_settings": record.export_settings,
                "file_size": record.file_size,
                "status": record.status,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None
            })
        
        logger.info(
            f"Retrieved {len(exports)} export records",
            correlation_id=correlation_id,
            total=total_count
        )
        
        return {
            "file_id": file_id,
            "exports": exports,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(
            f"Error getting export history: {str(e)}",
            correlation_id=correlation_id,
            file_id=file_id
        )
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/export-history/user/{user_id}")
async def get_user_export_history(
    user_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
    export_format: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get export history for a specific user across all files.
    
    Feature #514: Export history tracking
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    try:
        logger.info(
            f"Getting export history for user {user_id}",
            correlation_id=correlation_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
            format=export_format
        )
        
        from .models import ExportHistory
        
        # Build query
        query = db.query(ExportHistory).filter(
            ExportHistory.user_id == user_id
        )
        
        # Filter by format if specified
        if export_format:
            query = query.filter(ExportHistory.export_format == export_format)
        
        # Order by date and paginate
        history = query.order_by(
            ExportHistory.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        # Get total count
        total_query = db.query(func.count(ExportHistory.id)).filter(
            ExportHistory.user_id == user_id
        )
        if export_format:
            total_query = total_query.filter(ExportHistory.export_format == export_format)
        total_count = total_query.scalar()
        
        # Format response
        exports = []
        for record in history:
            exports.append({
                "id": record.id,
                "file_id": record.file_id,
                "user_id": record.user_id,
                "export_format": record.export_format,
                "export_type": record.export_type,
                "export_settings": record.export_settings,
                "file_size": record.file_size,
                "status": record.status,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "expires_at": record.expires_at.isoformat() if record.expires_at else None
            })
        
        logger.info(
            f"Retrieved {len(exports)} export records for user",
            correlation_id=correlation_id,
            total=total_count
        )
        
        return {
            "user_id": user_id,
            "exports": exports,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "format_filter": export_format
        }
        
    except Exception as e:
        logger.error(
            f"Error getting user export history: {str(e)}",
            correlation_id=correlation_id,
            user_id=user_id
        )
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("DIAGRAM_SERVICE_PORT", "8082")))


# ============================================================================
# ENTERPRISE ANALYTICS ENDPOINTS
# Features: Usage analytics for diagrams, users, and storage
# ============================================================================

@app.get("/api/analytics/overview")
async def get_analytics_overview(
    request: Request,
    team_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get overall usage analytics.
    
    Features:
    - Enterprise: Usage analytics: diagrams created
    - Enterprise: Usage analytics: users active  
    - Enterprise: Usage analytics: storage used
    - Enterprise: Cost allocation: track usage by team
    """
    try:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Total diagrams created
        total_diagrams_query = db.query(func.count(File.id))
        if team_id:
            total_diagrams_query = total_diagrams_query.filter(File.team_id == team_id)
        total_diagrams = total_diagrams_query.scalar() or 0
        
        # Diagrams created in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_diagrams_query = db.query(func.count(File.id)).filter(
            File.created_at >= thirty_days_ago
        )
        if team_id:
            recent_diagrams_query = recent_diagrams_query.filter(File.team_id == team_id)
        recent_diagrams = recent_diagrams_query.scalar() or 0
        
        # Active users (users who created or updated diagrams in last 30 days)
        active_users_query = db.query(func.count(func.distinct(File.owner_id))).filter(
            or_(
                File.created_at >= thirty_days_ago,
                File.updated_at >= thirty_days_ago
            )
        )
        if team_id:
            active_users_query = active_users_query.filter(File.team_id == team_id)
        active_users = active_users_query.scalar() or 0
        
        # Total users
        total_users_query = db.query(func.count(func.distinct(File.owner_id)))
        if team_id:
            total_users_query = total_users_query.filter(File.team_id == team_id)
        total_users = total_users_query.scalar() or 0
        
        # Storage used (estimate based on canvas_data and note_content size)
        # For production, you'd want to track actual file sizes
        storage_query = db.query(
            func.sum(
                func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
            )
        )
        if team_id:
            storage_query = storage_query.filter(File.team_id == team_id)
        storage_bytes = storage_query.scalar() or 0
        
        # Convert to MB
        storage_mb = storage_bytes / (1024 * 1024)
        
        # Diagram types breakdown
        diagram_types = {}
        types_query = db.query(
            File.file_type,
            func.count(File.id)
        ).group_by(File.file_type)
        if team_id:
            types_query = types_query.filter(File.team_id == team_id)
        
        for diagram_type, count in types_query.all():
            diagram_types[diagram_type or 'unknown'] = count
        
        # Team-specific cost allocation if requested
        team_breakdown = None
        if not team_id:
            # Get breakdown by team
            teams_query = db.query(
                Team.id,
                Team.name,
                func.count(File.id).label('diagram_count'),
                func.sum(
                    func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
                ).label('storage_bytes')
            ).join(
                File, File.team_id == Team.id, isouter=True
            ).group_by(Team.id, Team.name).all()
            
            team_breakdown = []
            for team_id_val, team_name, diagram_count, team_storage_bytes in teams_query:
                team_storage_mb = (team_storage_bytes or 0) / (1024 * 1024)
                team_breakdown.append({
                    "team_id": team_id_val,
                    "team_name": team_name,
                    "diagram_count": diagram_count or 0,
                    "storage_mb": round(team_storage_mb, 2)
                })
        
        logger.info(
            "Retrieved analytics overview",
            correlation_id=correlation_id,
            total_diagrams=total_diagrams,
            active_users=active_users
        )
        
        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "period": "all_time" if not team_id else f"team_{team_id}",
            "diagrams": {
                "total": total_diagrams,
                "last_30_days": recent_diagrams,
                "by_type": diagram_types
            },
            "users": {
                "total": total_users,
                "active_last_30_days": active_users
            },
            "storage": {
                "total_mb": round(storage_mb, 2),
                "total_gb": round(storage_mb / 1024, 2)
            }
        }
        
        if team_breakdown:
            response["team_breakdown"] = team_breakdown
        
        return response
        
    except Exception as e:
        logger.error(
            f"Error retrieving analytics overview: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/analytics/diagrams-created")
async def get_diagrams_created_analytics(
    request: Request,
    days: int = 30,
    team_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get diagrams created over time.
    Feature: Enterprise: Usage analytics: diagrams created
    """
    try:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Get diagrams created per day for the specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(
            func.date(File.created_at).label('date'),
            func.count(File.id).label('count')
        ).filter(
            File.created_at >= start_date
        ).group_by(
            func.date(File.created_at)
        ).order_by('date')
        
        if team_id:
            query = query.filter(File.team_id == team_id)
        
        results = query.all()
        
        # Format response
        daily_counts = []
        for date_val, count in results:
            daily_counts.append({
                "date": str(date_val),
                "count": count
            })
        
        # Calculate totals
        total = sum(item['count'] for item in daily_counts)
        avg_per_day = total / days if days > 0 else 0
        
        return {
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "total_diagrams_created": total,
            "average_per_day": round(avg_per_day, 2),
            "daily_counts": daily_counts
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving diagrams created analytics: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/analytics/users-active")
async def get_users_active_analytics(
    request: Request,
    days: int = 30,
    team_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get active users over time.
    Feature: Enterprise: Usage analytics: users active
    """
    try:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Get active users per day
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Users who created or updated diagrams each day
        query = db.query(
            func.date(func.coalesce(File.updated_at, File.created_at)).label('date'),
            func.count(func.distinct(File.owner_id)).label('active_users')
        ).filter(
            func.coalesce(File.updated_at, File.created_at) >= start_date
        ).group_by(
            func.date(func.coalesce(File.updated_at, File.created_at))
        ).order_by('date')
        
        if team_id:
            query = query.filter(File.team_id == team_id)
        
        results = query.all()
        
        # Format response
        daily_active = []
        for date_val, count in results:
            daily_active.append({
                "date": str(date_val),
                "active_users": count
            })
        
        # Calculate averages
        total_active_unique = db.query(
            func.count(func.distinct(File.owner_id))
        ).filter(
            func.coalesce(File.updated_at, File.created_at) >= start_date
        )
        if team_id:
            total_active_unique = total_active_unique.filter(File.team_id == team_id)
        
        unique_active_users = total_active_unique.scalar() or 0
        avg_daily_active = sum(item['active_users'] for item in daily_active) / days if days > 0 else 0
        
        return {
            "period_days": days,
            "start_date": start_date.date().isoformat(),
            "end_date": datetime.utcnow().date().isoformat(),
            "unique_active_users": unique_active_users,
            "average_daily_active": round(avg_daily_active, 2),
            "daily_active_users": daily_active
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving active users analytics: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/analytics/storage-used")
async def get_storage_used_analytics(
    request: Request,
    team_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get storage usage analytics.
    Feature: Enterprise: Usage analytics: storage used
    """
    try:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Total storage query
        storage_query = db.query(
            func.sum(
                func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
            )
        )
        if team_id:
            storage_query = storage_query.filter(File.team_id == team_id)
        
        total_storage_bytes = storage_query.scalar() or 0
        
        # Storage by diagram type
        type_storage_query = db.query(
            File.file_type,
            func.count(File.id).label('diagram_count'),
            func.sum(
                func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
            ).label('storage_bytes')
        ).group_by(File.file_type)
        
        if team_id:
            type_storage_query = type_storage_query.filter(File.team_id == team_id)
        
        by_type = []
        for diagram_type, count, storage_bytes in type_storage_query.all():
            storage_mb = (storage_bytes or 0) / (1024 * 1024)
            by_type.append({
                "type": diagram_type or 'unknown',
                "diagram_count": count,
                "storage_mb": round(storage_mb, 2)
            })
        
        # Storage by user (top 10)
        user_storage_query = db.query(
            File.owner_id,
            User.email,
            func.count(File.id).label('diagram_count'),
            func.sum(
                func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
            ).label('storage_bytes')
        ).join(User, User.id == File.owner_id).group_by(
            File.owner_id, User.email
        ).order_by(
            func.sum(func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)).desc()
        ).limit(10)
        
        if team_id:
            user_storage_query = user_storage_query.filter(File.team_id == team_id)
        
        top_users = []
        for owner_id, email, count, storage_bytes in user_storage_query.all():
            storage_mb = (storage_bytes or 0) / (1024 * 1024)
            top_users.append({
                "user_id": owner_id,
                "email": email,
                "diagram_count": count,
                "storage_mb": round(storage_mb, 2)
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_storage": {
                "bytes": total_storage_bytes,
                "mb": round(total_storage_bytes / (1024 * 1024), 2),
                "gb": round(total_storage_bytes / (1024 * 1024 * 1024), 3)
            },
            "by_type": by_type,
            "top_users": top_users
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving storage analytics: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@app.get("/api/analytics/cost-allocation")
async def get_cost_allocation_analytics(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get cost allocation by team.
    Feature: Enterprise: Cost allocation: track usage by team
    """
    try:
        correlation_id = request.headers.get("x-correlation-id", str(uuid.uuid4()))
        
        # Get usage metrics per team
        teams_query = db.query(
            Team.id,
            Team.name,
            func.count(func.distinct(File.owner_id)).label('user_count'),
            func.count(File.id).label('diagram_count'),
            func.sum(
                func.coalesce(func.pg_column_size(File.canvas_data), 0) + func.coalesce(func.pg_column_size(File.note_content), 0)
            ).label('storage_bytes'),
            func.count(Version.id).label('version_count')
        ).outerjoin(
            File, File.team_id == Team.id
        ).outerjoin(
            Version, Version.file_id == File.id
        ).group_by(Team.id, Team.name).all()
        
        team_costs = []
        # Simple cost model: $1 per user, $0.10 per diagram, $0.01 per GB storage
        for team_id, team_name, user_count, diagram_count, storage_bytes, version_count in teams_query:
            storage_gb = (storage_bytes or 0) / (1024 * 1024 * 1024)
            
            # Calculate costs
            user_cost = (user_count or 0) * 1.0  # $1 per user
            diagram_cost = (diagram_count or 0) * 0.1  # $0.10 per diagram
            storage_cost = storage_gb * 0.01  # $0.01 per GB
            total_cost = user_cost + diagram_cost + storage_cost
            
            team_costs.append({
                "team_id": team_id,
                "team_name": team_name,
                "metrics": {
                    "users": user_count or 0,
                    "diagrams": diagram_count or 0,
                    "storage_gb": round(storage_gb, 3),
                    "versions": version_count or 0
                },
                "costs": {
                    "user_cost": round(user_cost, 2),
                    "diagram_cost": round(diagram_cost, 2),
                    "storage_cost": round(storage_cost, 2),
                    "total_cost": round(total_cost, 2)
                }
            })
        
        # Sort by total cost descending
        team_costs.sort(key=lambda x: x['costs']['total_cost'], reverse=True)
        
        # Calculate totals
        total_cost = sum(t['costs']['total_cost'] for t in team_costs)
        total_users = sum(t['metrics']['users'] for t in team_costs)
        total_diagrams = sum(t['metrics']['diagrams'] for t in team_costs)
        total_storage_gb = sum(t['metrics']['storage_gb'] for t in team_costs)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cost_model": {
                "per_user": 1.0,
                "per_diagram": 0.1,
                "per_gb_storage": 0.01,
                "currency": "USD"
            },
            "totals": {
                "teams": len(team_costs),
                "users": total_users,
                "diagrams": total_diagrams,
                "storage_gb": round(total_storage_gb, 3),
                "total_cost": round(total_cost, 2)
            },
            "teams": team_costs
        }
        
    except Exception as e:
        logger.error(
            f"Error retrieving cost allocation: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve cost allocation")


# ============================================================================
# DATA RETENTION CLEANUP ENDPOINT
# ============================================================================

class CleanupRequest(BaseModel):
    """Request to cleanup old data based on retention policy."""
    diagram_retention_days: int
    deleted_retention_days: int
    version_retention_days: int


@app.post("/admin/cleanup-old-data")
def cleanup_old_data(
    cleanup_req: CleanupRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Clean up old data based on retention policy.
    
    Feature #544: Enterprise: Data retention policies: auto-delete old data
    
    This endpoint is called by auth-service to perform cleanup operations.
    """
    correlation_id = request.headers.get("X-Correlation-ID")
    
    try:
        # Delete diagrams older than retention period (soft delete - move to trash)
        diagram_cutoff = datetime.now(timezone.utc) - timedelta(days=cleanup_req.diagram_retention_days)
        old_diagrams = db.query(File).filter(
            File.created_at < diagram_cutoff,
            File.is_deleted == False
        ).all()
        
        old_diagrams_count = len(old_diagrams)
        
        # Soft-delete old diagrams (move to trash)
        for diagram in old_diagrams:
            diagram.is_deleted = True
            diagram.deleted_at = datetime.now(timezone.utc)
        
        # Hard delete from trash (permanently delete)
        trash_cutoff = datetime.now(timezone.utc) - timedelta(days=cleanup_req.deleted_retention_days)
        deleted_from_trash = db.query(File).filter(
            File.is_deleted == True,
            File.deleted_at < trash_cutoff
        ).delete()
        
        # Delete old versions (keep current version)
        version_cutoff = datetime.now(timezone.utc) - timedelta(days=cleanup_req.version_retention_days)
        
        # Get all files and their current version numbers
        files_with_versions = db.query(File.id, File.current_version).all()
        file_current_versions = {f[0]: f[1] for f in files_with_versions}
        
        # Delete old versions that are not current
        deleted_versions = 0
        for file_id, current_version in file_current_versions.items():
            deleted = db.query(Version).filter(
                Version.file_id == file_id,
                Version.version_number != current_version,
                Version.created_at < version_cutoff
            ).delete(synchronize_session=False)
            deleted_versions += deleted
        
        db.commit()
        
        logger.info(
            "Data retention cleanup completed",
            correlation_id=correlation_id,
            old_diagrams_moved_to_trash=old_diagrams_count,
            deleted_from_trash=deleted_from_trash,
            old_versions_deleted=deleted_versions,
            diagram_cutoff=diagram_cutoff.isoformat(),
            trash_cutoff=trash_cutoff.isoformat(),
            version_cutoff=version_cutoff.isoformat()
        )
        
        return {
            "cleanup_results": {
                "old_diagrams_moved_to_trash": old_diagrams_count,
                "deleted_from_trash": deleted_from_trash,
                "old_versions_deleted": deleted_versions
            },
            "cutoff_dates": {
                "diagram_cutoff": diagram_cutoff.isoformat(),
                "trash_cutoff": trash_cutoff.isoformat(),
                "version_cutoff": version_cutoff.isoformat()
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(
            f"Error during data retention cleanup: {str(e)}",
            correlation_id=correlation_id
        )
        raise HTTPException(status_code=500, detail="Failed to cleanup old data")


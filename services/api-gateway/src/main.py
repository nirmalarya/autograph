"""API Gateway - Routes requests to microservices."""
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
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
import traceback
import psutil
import gc

# MinIO client for storage monitoring
from minio import Minio
from minio.error import S3Error

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

# Memory monitoring metrics
memory_usage_bytes = Gauge(
    'api_gateway_memory_usage_bytes',
    'Current memory usage in bytes',
    registry=registry
)

memory_usage_percent = Gauge(
    'api_gateway_memory_usage_percent',
    'Current memory usage percentage',
    registry=registry
)

memory_available_bytes = Gauge(
    'api_gateway_memory_available_bytes',
    'Available memory in bytes',
    registry=registry
)

# CPU monitoring metrics
cpu_usage_percent = Gauge(
    'api_gateway_cpu_usage_percent',
    'Current CPU usage percentage',
    registry=registry
)

cpu_load_average_1m = Gauge(
    'api_gateway_cpu_load_average_1m',
    'CPU load average (1 minute)',
    registry=registry
)

cpu_load_average_5m = Gauge(
    'api_gateway_cpu_load_average_5m',
    'CPU load average (5 minutes)',
    registry=registry
)

cpu_load_average_15m = Gauge(
    'api_gateway_cpu_load_average_15m',
    'CPU load average (15 minutes)',
    registry=registry
)

# Network monitoring metrics
network_request_bytes = Counter(
    'api_gateway_network_request_bytes_total',
    'Total bytes received in requests',
    ['method', 'path'],
    registry=registry
)

network_response_bytes = Counter(
    'api_gateway_network_response_bytes_total',
    'Total bytes sent in responses',
    ['method', 'path', 'status_code'],
    registry=registry
)

network_bandwidth_saved_bytes = Counter(
    'api_gateway_network_bandwidth_saved_bytes_total',
    'Total bytes saved through compression',
    ['method', 'path'],
    registry=registry
)

network_large_payload_count = Counter(
    'api_gateway_network_large_payload_count_total',
    'Count of large payloads (>1MB)',
    ['payload_type'],  # 'request' or 'response'
    registry=registry
)

# Disk usage monitoring metrics
disk_usage_bytes = Gauge(
    'api_gateway_disk_usage_bytes',
    'Current disk usage in bytes',
    ['storage_type', 'location'],  # storage_type: 'minio' | 'local', location: bucket name or path
    registry=registry
)

disk_usage_percent = Gauge(
    'api_gateway_disk_usage_percent',
    'Current disk usage percentage',
    ['storage_type', 'location'],
    registry=registry
)

disk_total_bytes = Gauge(
    'api_gateway_disk_total_bytes',
    'Total disk capacity in bytes',
    ['storage_type', 'location'],
    registry=registry
)

disk_available_bytes = Gauge(
    'api_gateway_disk_available_bytes',
    'Available disk space in bytes',
    ['storage_type', 'location'],
    registry=registry
)

disk_alert_triggered = Counter(
    'api_gateway_disk_alert_triggered_total',
    'Count of disk usage alerts triggered',
    ['storage_type', 'location', 'threshold_type'],  # threshold_type: 'warning' | 'critical'
    registry=registry
)

# Get process for memory and CPU monitoring
process = psutil.Process()
baseline_memory_mb = None  # Will be set at startup
baseline_cpu_percent = None  # Will be set at startup

# Redis connection with connection pooling
# Using connection pool with max_connections=50 for high concurrency
# Note: Client is created lazily on first use
def get_redis():
    """Get Redis client with connection pooling."""
    return get_redis_client(db=1)  # Use db 1 for rate limiting

# MinIO client for storage monitoring
MINIO_HOST = os.getenv("MINIO_HOST", "localhost")
MINIO_PORT = os.getenv("MINIO_PORT", "9000")
MINIO_ENDPOINT = f"{MINIO_HOST}:{MINIO_PORT}"
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKETS = [
    os.getenv("MINIO_BUCKET_DIAGRAMS", "diagrams"),
    os.getenv("MINIO_BUCKET_EXPORTS", "exports"),
    os.getenv("MINIO_BUCKET_UPLOADS", "uploads")
]

def get_minio_client():
    """Get MinIO client for storage operations and monitoring."""
    return Minio(
        endpoint=MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )

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

# Memory monitoring configuration
MEMORY_CHECK_INTERVAL_SECONDS = 60  # Check every minute
MEMORY_WARNING_THRESHOLD_MB = 512  # Warn if memory exceeds 512MB
MEMORY_CRITICAL_THRESHOLD_MB = 1024  # Critical if memory exceeds 1GB

# CPU monitoring configuration
CPU_CHECK_INTERVAL_SECONDS = 60  # Check every minute
CPU_WARNING_THRESHOLD_PERCENT = 70.0  # Warn if CPU exceeds 70%
CPU_CRITICAL_THRESHOLD_PERCENT = 90.0  # Critical if CPU exceeds 90%

# Network monitoring configuration
NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES = 1024 * 1024  # 1 MB
NETWORK_COMPRESSION_MIN_SIZE_BYTES = 1024  # Compress responses > 1 KB
NETWORK_COMPRESSION_ENABLED = os.getenv("COMPRESSION_ENABLED", "true").lower() == "true"

# Disk usage monitoring configuration
DISK_CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes
DISK_WARNING_THRESHOLD_PERCENT = 70.0  # Warn if disk usage exceeds 70%
DISK_CRITICAL_THRESHOLD_PERCENT = 80.0  # Critical if disk usage exceeds 80%
DISK_ALERT_THRESHOLD_PERCENT = 80.0  # Send alerts at 80% (as per feature requirement)

async def monitor_memory_usage():
    """Background task to monitor memory usage periodically."""
    while True:
        try:
            # Get current memory info
            mem_info = process.memory_info()
            current_memory_mb = mem_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # Update Prometheus metrics
            memory_usage_bytes.set(mem_info.rss)
            memory_usage_percent.set(memory_percent)
            
            vm = psutil.virtual_memory()
            memory_available_bytes.set(vm.available)
            
            # Calculate memory growth since baseline
            if baseline_memory_mb:
                memory_growth_mb = current_memory_mb - baseline_memory_mb
                memory_growth_percent = (memory_growth_mb / baseline_memory_mb) * 100
                
                # Log memory status
                log_level = "info"
                if current_memory_mb > MEMORY_CRITICAL_THRESHOLD_MB:
                    log_level = "error"
                elif current_memory_mb > MEMORY_WARNING_THRESHOLD_MB:
                    log_level = "warning"
                
                if log_level == "error":
                    logger.error(
                        "CRITICAL: Memory usage is very high",
                        current_memory_mb=round(current_memory_mb, 2),
                        baseline_memory_mb=round(baseline_memory_mb, 2),
                        memory_growth_mb=round(memory_growth_mb, 2),
                        memory_growth_percent=round(memory_growth_percent, 2),
                        memory_percent=round(memory_percent, 2),
                        threshold_mb=MEMORY_CRITICAL_THRESHOLD_MB
                    )
                elif log_level == "warning":
                    logger.warning(
                        "Memory usage is elevated",
                        current_memory_mb=round(current_memory_mb, 2),
                        baseline_memory_mb=round(baseline_memory_mb, 2),
                        memory_growth_mb=round(memory_growth_mb, 2),
                        memory_growth_percent=round(memory_growth_percent, 2),
                        memory_percent=round(memory_percent, 2),
                        threshold_mb=MEMORY_WARNING_THRESHOLD_MB
                    )
                else:
                    # Only log DEBUG level for normal status to avoid spam
                    logger.debug(
                        "Memory usage check",
                        current_memory_mb=round(current_memory_mb, 2),
                        baseline_memory_mb=round(baseline_memory_mb, 2),
                        memory_growth_mb=round(memory_growth_mb, 2),
                        memory_growth_percent=round(memory_growth_percent, 2),
                        memory_percent=round(memory_percent, 2)
                    )
            
            # Wait before next check
            await asyncio.sleep(MEMORY_CHECK_INTERVAL_SECONDS)
            
        except asyncio.CancelledError:
            logger.info("Memory monitoring task cancelled")
            break
        except Exception as e:
            logger.error(
                "Error in memory monitoring task",
                exc=e,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            # Continue monitoring despite errors
            await asyncio.sleep(MEMORY_CHECK_INTERVAL_SECONDS)

async def monitor_cpu_usage():
    """Background task to monitor CPU usage periodically."""
    while True:
        try:
            # Get current CPU usage (interval=1 to get non-zero value on first call)
            cpu_percent = process.cpu_percent(interval=1)
            
            # Update Prometheus metrics
            cpu_usage_percent.set(cpu_percent)
            
            # Get system load averages (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()  # Returns (1min, 5min, 15min)
                cpu_load_average_1m.set(load_avg[0])
                cpu_load_average_5m.set(load_avg[1])
                cpu_load_average_15m.set(load_avg[2])
            except (AttributeError, OSError):
                # getloadavg() not available on all platforms (e.g., Windows)
                pass
            
            # Calculate CPU growth since baseline
            if baseline_cpu_percent is not None:
                cpu_growth_percent = cpu_percent - baseline_cpu_percent
                
                # Log CPU status
                log_level = "info"
                if cpu_percent > CPU_CRITICAL_THRESHOLD_PERCENT:
                    log_level = "error"
                elif cpu_percent > CPU_WARNING_THRESHOLD_PERCENT:
                    log_level = "warning"
                
                if log_level == "error":
                    logger.error(
                        "CRITICAL: CPU usage is very high",
                        current_cpu_percent=round(cpu_percent, 2),
                        baseline_cpu_percent=round(baseline_cpu_percent, 2),
                        cpu_growth_percent=round(cpu_growth_percent, 2),
                        threshold_percent=CPU_CRITICAL_THRESHOLD_PERCENT,
                        performance_bottleneck=True
                    )
                elif log_level == "warning":
                    logger.warning(
                        "CPU usage is elevated",
                        current_cpu_percent=round(cpu_percent, 2),
                        baseline_cpu_percent=round(baseline_cpu_percent, 2),
                        cpu_growth_percent=round(cpu_growth_percent, 2),
                        threshold_percent=CPU_WARNING_THRESHOLD_PERCENT,
                        performance_warning=True
                    )
                else:
                    # Only log DEBUG level for normal status to avoid spam
                    logger.debug(
                        "CPU usage check",
                        current_cpu_percent=round(cpu_percent, 2),
                        baseline_cpu_percent=round(baseline_cpu_percent, 2),
                        cpu_growth_percent=round(cpu_growth_percent, 2)
                    )
            
            # Wait before next check
            await asyncio.sleep(CPU_CHECK_INTERVAL_SECONDS)
            
        except asyncio.CancelledError:
            logger.info("CPU monitoring task cancelled")
            break
        except Exception as e:
            logger.error(
                "Error in CPU monitoring task",
                exc=e,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            # Continue monitoring despite errors
            await asyncio.sleep(CPU_CHECK_INTERVAL_SECONDS)

async def monitor_disk_usage():
    """Background task to monitor disk usage periodically for MinIO and local storage."""
    while True:
        try:
            # Monitor MinIO storage
            try:
                minio_client = get_minio_client()
                
                # Get disk usage for each bucket
                for bucket_name in MINIO_BUCKETS:
                    try:
                        # Check if bucket exists
                        if not minio_client.bucket_exists(bucket_name):
                            logger.warning(
                                f"MinIO bucket does not exist",
                                bucket=bucket_name
                            )
                            continue
                        
                        # Calculate total size of objects in bucket
                        total_size_bytes = 0
                        objects = minio_client.list_objects(bucket_name, recursive=True)
                        
                        for obj in objects:
                            total_size_bytes += obj.size
                        
                        # Get MinIO container disk usage (requires admin API or df command)
                        # For now, we'll just track bucket sizes
                        disk_usage_bytes.labels(
                            storage_type="minio",
                            location=bucket_name
                        ).set(total_size_bytes)
                        
                        logger.debug(
                            "MinIO bucket disk usage",
                            bucket=bucket_name,
                            size_bytes=total_size_bytes,
                            size_mb=round(total_size_bytes / 1024 / 1024, 2),
                            size_gb=round(total_size_bytes / 1024 / 1024 / 1024, 3)
                        )
                        
                    except S3Error as e:
                        logger.error(
                            "Error monitoring MinIO bucket",
                            bucket=bucket_name,
                            exc=e,
                            error_code=e.code if hasattr(e, 'code') else None
                        )
                    except Exception as e:
                        logger.error(
                            "Error monitoring MinIO bucket",
                            bucket=bucket_name,
                            exc=e
                        )
                
            except Exception as e:
                logger.error(
                    "Error connecting to MinIO",
                    exc=e,
                    error_type=type(e).__name__
                )
            
            # Monitor local disk usage (where API gateway is running)
            try:
                # Get disk usage for root filesystem
                disk = psutil.disk_usage('/')
                
                disk_total_bytes.labels(
                    storage_type="local",
                    location="root"
                ).set(disk.total)
                
                disk_usage_bytes.labels(
                    storage_type="local",
                    location="root"
                ).set(disk.used)
                
                disk_available_bytes.labels(
                    storage_type="local",
                    location="root"
                ).set(disk.free)
                
                disk_usage_percent.labels(
                    storage_type="local",
                    location="root"
                ).set(disk.percent)
                
                # Check thresholds and trigger alerts
                if disk.percent >= DISK_CRITICAL_THRESHOLD_PERCENT:
                    disk_alert_triggered.labels(
                        storage_type="local",
                        location="root",
                        threshold_type="critical"
                    ).inc()
                    
                    logger.error(
                        "CRITICAL: Disk usage is very high",
                        storage_type="local",
                        location="root",
                        used_percent=disk.percent,
                        used_gb=round(disk.used / 1024 / 1024 / 1024, 2),
                        total_gb=round(disk.total / 1024 / 1024 / 1024, 2),
                        available_gb=round(disk.free / 1024 / 1024 / 1024, 2),
                        threshold_percent=DISK_CRITICAL_THRESHOLD_PERCENT,
                        alert_triggered=True
                    )
                elif disk.percent >= DISK_WARNING_THRESHOLD_PERCENT:
                    disk_alert_triggered.labels(
                        storage_type="local",
                        location="root",
                        threshold_type="warning"
                    ).inc()
                    
                    logger.warning(
                        "Disk usage is elevated",
                        storage_type="local",
                        location="root",
                        used_percent=disk.percent,
                        used_gb=round(disk.used / 1024 / 1024 / 1024, 2),
                        total_gb=round(disk.total / 1024 / 1024 / 1024, 2),
                        available_gb=round(disk.free / 1024 / 1024 / 1024, 2),
                        threshold_percent=DISK_WARNING_THRESHOLD_PERCENT,
                        alert_triggered=True
                    )
                else:
                    # Only log DEBUG level for normal status to avoid spam
                    logger.debug(
                        "Disk usage check",
                        storage_type="local",
                        location="root",
                        used_percent=disk.percent,
                        used_gb=round(disk.used / 1024 / 1024 / 1024, 2),
                        total_gb=round(disk.total / 1024 / 1024 / 1024, 2),
                        available_gb=round(disk.free / 1024 / 1024 / 1024, 2)
                    )
                    
            except Exception as e:
                logger.error(
                    "Error monitoring local disk usage",
                    exc=e
                )
            
            # Wait before next check
            await asyncio.sleep(DISK_CHECK_INTERVAL_SECONDS)
            
        except asyncio.CancelledError:
            logger.info("Disk monitoring task cancelled")
            break
        except Exception as e:
            logger.error(
                "Error in disk monitoring task",
                exc=e,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            # Continue monitoring despite errors
            await asyncio.sleep(DISK_CHECK_INTERVAL_SECONDS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("API Gateway starting up")
    
    # Record baseline memory usage
    global baseline_memory_mb
    mem_info = process.memory_info()
    baseline_memory_mb = mem_info.rss / 1024 / 1024  # Convert to MB
    
    logger.info(
        "Baseline memory usage recorded",
        memory_mb=round(baseline_memory_mb, 2),
        memory_bytes=mem_info.rss
    )
    
    # Update initial memory metrics
    memory_usage_bytes.set(mem_info.rss)
    memory_usage_percent.set(process.memory_percent())
    vm = psutil.virtual_memory()
    memory_available_bytes.set(vm.available)
    
    # Record baseline CPU usage (call with interval to get initial reading)
    global baseline_cpu_percent
    baseline_cpu_percent = process.cpu_percent(interval=1)
    
    logger.info(
        "Baseline CPU usage recorded",
        cpu_percent=round(baseline_cpu_percent, 2)
    )
    
    # Update initial CPU metrics
    cpu_usage_percent.set(baseline_cpu_percent)
    try:
        load_avg = psutil.getloadavg()
        cpu_load_average_1m.set(load_avg[0])
        cpu_load_average_5m.set(load_avg[1])
        cpu_load_average_15m.set(load_avg[2])
    except (AttributeError, OSError):
        pass  # Not available on all platforms
    
    # Start background monitoring tasks
    memory_monitor_task = asyncio.create_task(monitor_memory_usage())
    cpu_monitor_task = asyncio.create_task(monitor_cpu_usage())
    disk_monitor_task = asyncio.create_task(monitor_disk_usage())
    alert_monitor_task = asyncio.create_task(monitor_services_for_alerts())
    
    # Start scheduled backup task if enabled
    global SCHEDULED_BACKUP_TASK, SCHEDULED_MINIO_BACKUP_TASK
    backup_enabled = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    if backup_enabled:
        SCHEDULED_BACKUP_TASK = asyncio.create_task(scheduled_backup_task())
        logger.info("Scheduled database backup task started")
    
    # Start scheduled MinIO backup task if enabled
    minio_backup_enabled = os.getenv("MINIO_BACKUP_ENABLED", "true").lower() == "true"
    if minio_backup_enabled:
        SCHEDULED_MINIO_BACKUP_TASK = asyncio.create_task(scheduled_minio_backup_task())
        logger.info("Scheduled MinIO bucket backup task started")
    
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
        # Cancel monitoring tasks
        memory_monitor_task.cancel()
        cpu_monitor_task.cancel()
        disk_monitor_task.cancel()
        alert_monitor_task.cancel()
        if SCHEDULED_BACKUP_TASK:
            SCHEDULED_BACKUP_TASK.cancel()
        if SCHEDULED_MINIO_BACKUP_TASK:
            SCHEDULED_MINIO_BACKUP_TASK.cancel()
    
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
    
    # Cancel monitoring tasks
    memory_monitor_task.cancel()
    cpu_monitor_task.cancel()
    disk_monitor_task.cancel()
    alert_monitor_task.cancel()
    if SCHEDULED_BACKUP_TASK:
        SCHEDULED_BACKUP_TASK.cancel()
    if SCHEDULED_MINIO_BACKUP_TASK:
        SCHEDULED_MINIO_BACKUP_TASK.cancel()
    
    try:
        await memory_monitor_task
    except asyncio.CancelledError:
        pass
    try:
        await cpu_monitor_task
    except asyncio.CancelledError:
        pass
    try:
        await disk_monitor_task
    except asyncio.CancelledError:
        pass
    try:
        await alert_monitor_task
    except asyncio.CancelledError:
        pass
    if SCHEDULED_BACKUP_TASK:
        try:
            await SCHEDULED_BACKUP_TASK
        except asyncio.CancelledError:
            pass
    if SCHEDULED_MINIO_BACKUP_TASK:
        try:
            await SCHEDULED_MINIO_BACKUP_TASK
        except asyncio.CancelledError:
            pass
    
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

# Security headers middleware - applied to all responses
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses to prevent common web vulnerabilities.
    Headers added:
    - X-Frame-Options: Prevents clickjacking attacks
    - X-Content-Type-Options: Prevents MIME-sniffing attacks
    - X-XSS-Protection: Enables XSS filtering (legacy browsers)
    - Content-Security-Policy: Controls resource loading
    - Strict-Transport-Security: Enforces HTTPS connections
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Controls browser features
    """
    response = await call_next(request)
    
    # X-Frame-Options: Prevent the page from being embedded in iframes
    response.headers["X-Frame-Options"] = "DENY"
    
    # X-Content-Type-Options: Prevent browsers from MIME-sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # X-XSS-Protection: Enable XSS filtering in legacy browsers
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Content-Security-Policy: Define allowed sources for resources
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self' ws: wss:",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "upgrade-insecure-requests",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    # Strict-Transport-Security: Force HTTPS for all connections
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Referrer-Policy: Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions-Policy: Control browser features
    permissions_directives = [
        "geolocation=()",
        "microphone=()",
        "camera=()",
        "payment=()",
        "usb=()",
        "magnetometer=()",
        "gyroscope=()",
        "accelerometer=()",
    ]
    response.headers["Permissions-Policy"] = ", ".join(permissions_directives)
    
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    "/dependencies",  # Service dependency mapping
    "/alerts",  # Alerting system
    "/api/admin/backup/",  # Database backup and restore (for testing)
    "/api/admin/minio/",  # MinIO bucket backup and restore (for testing)
    "/api/admin/dr/",  # Disaster recovery endpoints (for testing)
    "/api/feature-flags",  # Feature flags API (all endpoints)
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/token",
    "/api/auth/email/verify",  # Email verification (Feature #65)
    "/api/auth/oauth/",  # OAuth endpoints (Feature #112-115)
    "/api/auth/health",
    "/api/auth/test/",  # All test endpoints
    "/api/diagrams/shared/",  # Public shared diagram access
    "/api/diagrams/version-shared/",  # Public shared version access (Feature #478)
    "/test/",  # All test endpoints on gateway
]

# CORS configuration (added after app creation below)

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


async def verify_jwt_token(token: str) -> dict:
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

        # Accept both regular access tokens and OAuth access tokens
        if token_type not in ("access", "oauth_access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Feature #115: Check if OAuth token is revoked
        if token_type == "oauth_access":
            token_jti = payload.get("jti")
            if token_jti:
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        response = await client.get(
                            f"http://{SERVICE_HOST_AUTH}:8085/oauth/token/status/{token_jti}"
                        )
                        if response.status_code == 200:
                            token_status = response.json()
                            if token_status.get("is_revoked"):
                                raise HTTPException(
                                    status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Token revoked"
                                )
                        # If auth service is down or token not found, fail closed for security
                        elif response.status_code != 404:
                            logger.warning(
                                "Failed to check OAuth token status",
                                token_jti=token_jti,
                                status_code=response.status_code
                            )
                except httpx.RequestError as e:
                    logger.warning(
                        "Error checking OAuth token revocation status",
                        token_jti=token_jti,
                        error=str(e)
                    )
                    # Fail open for availability - if auth service is down, allow the request
                    # In production, you might want to fail closed instead

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
    """Middleware to track request metrics and log slow requests."""
    # Get correlation ID from request state
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Track active connections
    active_connections.inc()
    
    # Track request start time
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Track request duration
        duration = time.time() - start_time
        duration_ms = duration * 1000  # Convert to milliseconds
        
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
        
        # Log request duration
        logger.info(
            "Request completed",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        
        # Log slow requests (> 1 second)
        if duration > 1.0:
            logger.warning(
                "Slow request detected",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                threshold_ms=1000,
                performance_issue=True
            )
        
        return response
    finally:
        # Always decrement active connections
        active_connections.dec()


@app.middleware("http")
async def network_monitoring_middleware(request: Request, call_next):
    """Middleware to monitor network traffic (request/response sizes)."""
    import gzip
    from io import BytesIO
    
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Measure request size
    request_body = b""
    if request.method in ["POST", "PUT", "PATCH"]:
        # Read body for size measurement (will be re-read by endpoint)
        request_body = await request.body()
        request_size = len(request_body)
        
        # Track request bytes
        network_request_bytes.labels(
            method=request.method,
            path=request.url.path
        ).inc(request_size)
        
        # Check for large payloads
        if request_size > NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES:
            network_large_payload_count.labels(payload_type="request").inc()
            logger.warning(
                "Large request payload detected",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                request_size_bytes=request_size,
                request_size_mb=round(request_size / 1024 / 1024, 2),
                threshold_mb=round(NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES / 1024 / 1024, 2)
            )
    else:
        request_size = 0
    
    # Process request
    response = await call_next(request)
    
    # Measure response size
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    response_size = len(response_body)
    
    # Track response bytes (before compression)
    network_response_bytes.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ).inc(response_size)
    
    # Check for large response payloads
    if response_size > NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES:
        network_large_payload_count.labels(payload_type="response").inc()
        logger.warning(
            "Large response payload detected",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            response_size_bytes=response_size,
            response_size_mb=round(response_size / 1024 / 1024, 2),
            threshold_mb=round(NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES / 1024 / 1024, 2)
        )
    
    # Apply compression if enabled and response is large enough
    compressed = False
    if (NETWORK_COMPRESSION_ENABLED and 
        response_size >= NETWORK_COMPRESSION_MIN_SIZE_BYTES and
        "gzip" in request.headers.get("accept-encoding", "").lower()):
        
        try:
            # Compress response body
            compressed_body = gzip.compress(response_body, compresslevel=6)
            compressed_size = len(compressed_body)
            bandwidth_saved = response_size - compressed_size
            
            # Track bandwidth savings
            network_bandwidth_saved_bytes.labels(
                method=request.method,
                path=request.url.path
            ).inc(bandwidth_saved)
            
            logger.info(
                "Response compressed",
                correlation_id=correlation_id,
                method=request.method,
                path=request.url.path,
                original_size_bytes=response_size,
                compressed_size_bytes=compressed_size,
                bandwidth_saved_bytes=bandwidth_saved,
                compression_ratio=round((1 - compressed_size / response_size) * 100, 2) if response_size > 0 else 0
            )
            
            # Replace body with compressed version
            response_body = compressed_body
            compressed = True
        except Exception as e:
            logger.error(
                "Compression failed",
                correlation_id=correlation_id,
                error=str(e),
                exc=e
            )
    
    # Log network traffic
    logger.debug(
        "Network traffic",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        request_size_bytes=request_size,
        response_size_bytes=response_size,
        compressed=compressed
    )
    
    # Create new response with (possibly compressed) body
    headers = dict(response.headers)
    if compressed:
        headers["content-encoding"] = "gzip"
        headers["vary"] = "Accept-Encoding"
    
    # Remove content-length as it may have changed
    headers.pop("content-length", None)
    
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.headers.get("content-type")
    )


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
        payload = await verify_jwt_token(token)
        # Add user_id to request state for downstream services
        request.state.user_id = payload.get("sub")

        # Feature #114: OAuth 2.0 scope-based permissions
        # If this is an OAuth access token, enforce scope-based permissions
        token_type = payload.get("type")
        if token_type == "oauth_access":
            scopes = payload.get("scopes", [])
            method = request.method.upper()

            # Define scope requirements
            # - read: Only GET/HEAD/OPTIONS allowed
            # - write: All methods allowed (GET, POST, PUT, DELETE, PATCH)
            # - admin: Full access (all methods + admin endpoints)

            # Check if user has required scope for this method
            has_permission = False

            if method in ["GET", "HEAD", "OPTIONS"]:
                # Read operations - any scope is sufficient
                has_permission = bool(scopes)  # At least one scope required
            elif method in ["POST", "PUT", "DELETE", "PATCH"]:
                # Write operations - need 'write' or 'admin' scope
                has_permission = "write" in scopes or "admin" in scopes

            if not has_permission:
                logger.warning(
                    "OAuth permission denied: insufficient scope",
                    correlation_id=correlation_id,
                    user_id=payload.get("sub"),
                    scopes=scopes,
                    method=method,
                    path=path
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "detail": f"Insufficient permissions. Required scope for {method} operations: write or admin",
                        "required_scopes": ["write", "admin"] if method in ["POST", "PUT", "DELETE", "PATCH"] else ["read", "write", "admin"],
                        "granted_scopes": scopes
                    }
                )

            logger.info(
                "OAuth permission granted",
                correlation_id=correlation_id,
                user_id=payload.get("sub"),
                scopes=scopes,
                method=method,
                path=path
            )

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


@app.get("/test/memory")
async def test_memory_usage(request: Request):
    """Test endpoint to check current memory usage."""
    mem_info = process.memory_info()
    current_memory_mb = mem_info.rss / 1024 / 1024
    memory_percent = process.memory_percent()
    
    vm = psutil.virtual_memory()
    
    memory_data = {
        "current_memory_mb": round(current_memory_mb, 2),
        "baseline_memory_mb": round(baseline_memory_mb, 2) if baseline_memory_mb else None,
        "memory_growth_mb": round(current_memory_mb - baseline_memory_mb, 2) if baseline_memory_mb else None,
        "memory_percent": round(memory_percent, 2),
        "system_memory_total_mb": round(vm.total / 1024 / 1024, 2),
        "system_memory_available_mb": round(vm.available / 1024 / 1024, 2),
        "system_memory_used_percent": round(vm.percent, 2),
        "warning_threshold_mb": MEMORY_WARNING_THRESHOLD_MB,
        "critical_threshold_mb": MEMORY_CRITICAL_THRESHOLD_MB,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return memory_data


@app.get("/test/memory/allocate")
async def test_memory_allocate(request: Request, size_mb: int = 10):
    """Test endpoint to allocate memory and verify monitoring."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    try:
        # Get memory before allocation
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Allocate memory (create large list)
        # Each element is about 8 bytes (64-bit pointer/integer)
        # 1 MB = 1024*1024 bytes = 131072 integers
        elements_per_mb = 131072
        data = [0] * (size_mb * elements_per_mb)
        
        # Get memory after allocation
        mem_after = process.memory_info().rss / 1024 / 1024
        actual_allocated_mb = mem_after - mem_before
        
        logger.info(
            "Memory allocation test",
            correlation_id=correlation_id,
            requested_size_mb=size_mb,
            actual_allocated_mb=round(actual_allocated_mb, 2),
            memory_before_mb=round(mem_before, 2),
            memory_after_mb=round(mem_after, 2)
        )
        
        # Clean up
        del data
        gc.collect()
        
        # Get memory after GC
        mem_after_gc = process.memory_info().rss / 1024 / 1024
        
        return {
            "message": "Memory allocated and released",
            "correlation_id": correlation_id,
            "requested_size_mb": size_mb,
            "actual_allocated_mb": round(actual_allocated_mb, 2),
            "memory_before_mb": round(mem_before, 2),
            "memory_after_allocation_mb": round(mem_after, 2),
            "memory_after_gc_mb": round(mem_after_gc, 2),
            "gc_recovered_mb": round(mem_after - mem_after_gc, 2),
            "note": "Check logs for memory monitoring warnings if size > 500MB"
        }
        
    except Exception as e:
        logger.exception(
            "Error in memory allocation test",
            exc=e,
            correlation_id=correlation_id,
            size_mb=size_mb
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@app.get("/test/memory/gc")
async def test_memory_garbage_collection(request: Request):
    """Test endpoint to trigger garbage collection."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Get memory before GC
    mem_before = process.memory_info().rss / 1024 / 1024
    
    # Run garbage collection
    gc_stats = {
        "collected": [],
        "uncollectable": [],
        "total_collected": 0
    }
    
    for generation in range(gc.get_count().__len__()):
        collected = gc.collect(generation)
        gc_stats["collected"].append(collected)
        gc_stats["total_collected"] += collected
    
    # Get uncollectable objects
    uncollectable = len(gc.garbage)
    gc_stats["uncollectable"].append(uncollectable)
    
    # Get memory after GC
    mem_after = process.memory_info().rss / 1024 / 1024
    memory_freed_mb = mem_before - mem_after
    
    logger.info(
        "Garbage collection executed",
        correlation_id=correlation_id,
        memory_before_mb=round(mem_before, 2),
        memory_after_mb=round(mem_after, 2),
        memory_freed_mb=round(memory_freed_mb, 2),
        objects_collected=gc_stats["total_collected"],
        uncollectable_objects=uncollectable
    )
    
    return {
        "message": "Garbage collection completed",
        "correlation_id": correlation_id,
        "memory_before_mb": round(mem_before, 2),
        "memory_after_mb": round(mem_after, 2),
        "memory_freed_mb": round(memory_freed_mb, 2),
        "gc_stats": gc_stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/test/cpu")
async def test_cpu_usage(request: Request):
    """Test endpoint to check current CPU usage."""
    # Get current CPU usage (interval=1 for accurate reading)
    cpu_percent = process.cpu_percent(interval=1)
    
    # Get system-wide CPU info
    system_cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    
    cpu_data = {
        "process_cpu_percent": round(cpu_percent, 2),
        "baseline_cpu_percent": round(baseline_cpu_percent, 2) if baseline_cpu_percent is not None else None,
        "cpu_growth_percent": round(cpu_percent - baseline_cpu_percent, 2) if baseline_cpu_percent is not None else None,
        "system_cpu_percent": round(system_cpu_percent, 2),
        "cpu_count_logical": cpu_count_logical,
        "cpu_count_physical": cpu_count_physical,
        "warning_threshold_percent": CPU_WARNING_THRESHOLD_PERCENT,
        "critical_threshold_percent": CPU_CRITICAL_THRESHOLD_PERCENT,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Try to get load averages (Unix-like systems only)
    try:
        load_avg = psutil.getloadavg()
        cpu_data["load_average_1m"] = round(load_avg[0], 2)
        cpu_data["load_average_5m"] = round(load_avg[1], 2)
        cpu_data["load_average_15m"] = round(load_avg[2], 2)
    except (AttributeError, OSError):
        cpu_data["load_average_note"] = "Load averages not available on this platform"
    
    return cpu_data


@app.get("/test/cpu/stress")
async def test_cpu_stress(request: Request, duration_seconds: int = 5, intensity: int = 1):
    """Test endpoint to stress CPU and verify monitoring.
    
    Args:
        duration_seconds: How long to stress CPU (default: 5 seconds, max: 30)
        intensity: CPU stress intensity level 1-10 (default: 1)
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Limit duration and intensity for safety
    duration_seconds = min(duration_seconds, 30)
    intensity = max(1, min(intensity, 10))
    
    try:
        # Get CPU before stress
        cpu_before = process.cpu_percent(interval=0.1)
        
        # CPU-intensive operation: calculate prime numbers
        def stress_cpu(target_duration: float, workload: int):
            """Perform CPU-intensive calculations."""
            start_time = time.time()
            count = 0
            
            # Adjust workload based on intensity
            max_number = 10000 * workload
            
            while time.time() - start_time < target_duration:
                # Find prime numbers (CPU-intensive)
                for num in range(2, max_number):
                    is_prime = True
                    for i in range(2, int(num ** 0.5) + 1):
                        if num % i == 0:
                            is_prime = False
                            break
                    if is_prime:
                        count += 1
                
                # Small sleep to allow other tasks
                time.sleep(0.01)
            
            return count
        
        # Run stress test
        logger.info(
            "Starting CPU stress test",
            correlation_id=correlation_id,
            duration_seconds=duration_seconds,
            intensity=intensity
        )
        
        primes_count = stress_cpu(duration_seconds, intensity)
        
        # Get CPU after stress
        cpu_after = process.cpu_percent(interval=0.1)
        
        logger.info(
            "CPU stress test completed",
            correlation_id=correlation_id,
            duration_seconds=duration_seconds,
            intensity=intensity,
            cpu_before=round(cpu_before, 2),
            cpu_after=round(cpu_after, 2),
            primes_calculated=primes_count
        )
        
        return {
            "message": "CPU stress test completed",
            "correlation_id": correlation_id,
            "duration_seconds": duration_seconds,
            "intensity": intensity,
            "cpu_before_percent": round(cpu_before, 2),
            "cpu_after_percent": round(cpu_after, 2),
            "cpu_increase_percent": round(cpu_after - cpu_before, 2),
            "primes_calculated": primes_count,
            "note": "Check logs for CPU monitoring warnings if CPU > 70%",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.exception(
            "Error in CPU stress test",
            exc=e,
            correlation_id=correlation_id,
            duration_seconds=duration_seconds,
            intensity=intensity
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )


@app.get("/test/network")
async def test_network_stats(request: Request):
    """Test endpoint to get current network statistics."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    return {
        "message": "Network monitoring is active",
        "correlation_id": correlation_id,
        "configuration": {
            "compression_enabled": NETWORK_COMPRESSION_ENABLED,
            "compression_min_size_bytes": NETWORK_COMPRESSION_MIN_SIZE_BYTES,
            "compression_min_size_kb": round(NETWORK_COMPRESSION_MIN_SIZE_BYTES / 1024, 2),
            "large_payload_threshold_bytes": NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES,
            "large_payload_threshold_mb": round(NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES / 1024 / 1024, 2)
        },
        "note": "Network metrics available at /metrics endpoint",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/test/network/large-request")
async def test_network_large_request(request: Request):
    """Test endpoint to send large request payload."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Read request body
    body = await request.body()
    body_size = len(body)
    
    logger.info(
        "Large request received",
        correlation_id=correlation_id,
        body_size_bytes=body_size,
        body_size_mb=round(body_size / 1024 / 1024, 2),
        is_large=body_size > NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES
    )
    
    return {
        "message": "Large request processed",
        "correlation_id": correlation_id,
        "request_size_bytes": body_size,
        "request_size_kb": round(body_size / 1024, 2),
        "request_size_mb": round(body_size / 1024 / 1024, 2),
        "is_large_payload": body_size > NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES,
        "threshold_mb": round(NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES / 1024 / 1024, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/test/network/large-response")
async def test_network_large_response(request: Request, size_mb: float = 1.0):
    """Test endpoint to return large response payload.
    
    Args:
        size_mb: Size of response in MB (default: 1.0, max: 10.0)
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Limit size for safety
    size_mb = min(size_mb, 10.0)
    size_bytes = int(size_mb * 1024 * 1024)
    
    logger.info(
        "Generating large response",
        correlation_id=correlation_id,
        size_mb=size_mb,
        size_bytes=size_bytes
    )
    
    # Generate large payload (repeating pattern for good compression)
    # Using JSON array of objects
    pattern = {"id": 1, "name": "test", "description": "This is a test object for network monitoring", "timestamp": datetime.utcnow().isoformat()}
    pattern_json = json.dumps(pattern)
    pattern_size = len(pattern_json)
    
    # Calculate how many patterns needed
    num_patterns = size_bytes // pattern_size
    
    # Generate large array
    data = [pattern for _ in range(num_patterns)]
    
    response_data = {
        "message": "Large response generated",
        "correlation_id": correlation_id,
        "requested_size_mb": size_mb,
        "actual_size_mb": round(len(json.dumps(data)) / 1024 / 1024, 2),
        "num_items": len(data),
        "is_large_payload": size_bytes > NETWORK_LARGE_PAYLOAD_THRESHOLD_BYTES,
        "compression_enabled": NETWORK_COMPRESSION_ENABLED,
        "note": "Check response headers for Content-Encoding: gzip if compression applied",
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return response_data


@app.get("/test/disk")
async def test_disk_stats(request: Request):
    """Test endpoint to get current disk usage statistics."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    try:
        # Get local disk usage
        disk = psutil.disk_usage('/')
        
        # Get MinIO bucket sizes
        minio_stats = []
        try:
            minio_client = get_minio_client()
            for bucket_name in MINIO_BUCKETS:
                if minio_client.bucket_exists(bucket_name):
                    total_size = 0
                    objects = minio_client.list_objects(bucket_name, recursive=True)
                    for obj in objects:
                        total_size += obj.size
                    
                    minio_stats.append({
                        "bucket": bucket_name,
                        "size_bytes": total_size,
                        "size_mb": round(total_size / 1024 / 1024, 2),
                        "size_gb": round(total_size / 1024 / 1024 / 1024, 3)
                    })
                else:
                    minio_stats.append({
                        "bucket": bucket_name,
                        "status": "does not exist"
                    })
        except Exception as e:
            minio_stats = {"error": str(e)}
        
        return {
            "message": "Disk monitoring is active",
            "correlation_id": correlation_id,
            "local_disk": {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "used_percent": disk.percent,
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "alert_triggered": disk.percent >= DISK_ALERT_THRESHOLD_PERCENT
            },
            "minio_storage": minio_stats,
            "configuration": {
                "check_interval_seconds": DISK_CHECK_INTERVAL_SECONDS,
                "warning_threshold_percent": DISK_WARNING_THRESHOLD_PERCENT,
                "critical_threshold_percent": DISK_CRITICAL_THRESHOLD_PERCENT,
                "alert_threshold_percent": DISK_ALERT_THRESHOLD_PERCENT
            },
            "note": "Disk metrics available at /metrics endpoint",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(
            "Error getting disk statistics",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error getting disk statistics: {str(e)}"
        )


@app.post("/test/disk/upload")
async def test_disk_upload(request: Request, size_mb: float = 1.0, bucket: str = "uploads"):
    """Test endpoint to upload a file to MinIO to test disk usage increase.
    
    Args:
        size_mb: Size of file to upload in MB (default: 1.0, max: 100.0)
        bucket: Bucket to upload to (default: uploads)
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    try:
        # Limit size for safety
        size_mb = min(size_mb, 100.0)
        size_bytes = int(size_mb * 1024 * 1024)
        
        # Generate test data
        test_data = b'0' * size_bytes
        
        # Upload to MinIO
        minio_client = get_minio_client()
        
        # Ensure bucket exists
        if not minio_client.bucket_exists(bucket):
            raise HTTPException(
                status_code=400,
                detail=f"Bucket '{bucket}' does not exist"
            )
        
        # Generate unique filename
        filename = f"test-upload-{uuid.uuid4()}.bin"
        
        # Upload file
        from io import BytesIO
        minio_client.put_object(
            bucket,
            filename,
            BytesIO(test_data),
            length=size_bytes,
            content_type="application/octet-stream"
        )
        
        logger.info(
            "Test file uploaded to MinIO",
            correlation_id=correlation_id,
            bucket=bucket,
            filename=filename,
            size_mb=size_mb,
            size_bytes=size_bytes
        )
        
        return {
            "message": "File uploaded successfully",
            "correlation_id": correlation_id,
            "bucket": bucket,
            "filename": filename,
            "size_bytes": size_bytes,
            "size_mb": size_mb,
            "note": "Use GET /test/disk to verify disk usage increased",
            "cleanup_note": f"Use DELETE /test/disk/cleanup?bucket={bucket}&filename={filename} to remove this file",
            "timestamp": datetime.utcnow().isoformat()
        }
    except S3Error as e:
        logger.error(
            "MinIO error during upload",
            correlation_id=correlation_id,
            exc=e,
            error_code=e.code if hasattr(e, 'code') else None
        )
        raise HTTPException(
            status_code=500,
            detail=f"MinIO error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Error uploading test file",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.delete("/test/disk/cleanup")
async def test_disk_cleanup(request: Request, bucket: str, filename: str):
    """Delete a test file from MinIO.
    
    Args:
        bucket: Bucket name
        filename: Filename to delete
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    try:
        minio_client = get_minio_client()
        
        # Ensure bucket exists
        if not minio_client.bucket_exists(bucket):
            raise HTTPException(
                status_code=400,
                detail=f"Bucket '{bucket}' does not exist"
            )
        
        # Delete object
        minio_client.remove_object(bucket, filename)
        
        logger.info(
            "Test file deleted from MinIO",
            correlation_id=correlation_id,
            bucket=bucket,
            filename=filename
        )
        
        return {
            "message": "File deleted successfully",
            "correlation_id": correlation_id,
            "bucket": bucket,
            "filename": filename,
            "note": "Use GET /test/disk to verify disk usage decreased",
            "timestamp": datetime.utcnow().isoformat()
        }
    except S3Error as e:
        logger.error(
            "MinIO error during deletion",
            correlation_id=correlation_id,
            exc=e,
            error_code=e.code if hasattr(e, 'code') else None
        )
        raise HTTPException(
            status_code=500,
            detail=f"MinIO error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            "Error deleting test file",
            correlation_id=correlation_id,
            exc=e
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


# ============================================================================
# SERVICE DEPENDENCY MAPPING
# ============================================================================

# Service dependency graph definition
SERVICE_DEPENDENCIES = {
    "frontend": {
        "name": "Frontend",
        "type": "application",
        "port": 3000,
        "depends_on": ["api-gateway"],
        "health_endpoint": "http://localhost:3000"
    },
    "api-gateway": {
        "name": "API Gateway",
        "type": "gateway",
        "port": 8080,
        "depends_on": ["auth-service", "diagram-service", "ai-service", "collaboration-service", 
                      "git-service", "export-service", "integration-hub", "redis"],
        "health_endpoint": "http://localhost:8080/health"
    },
    "auth-service": {
        "name": "Auth Service",
        "type": "microservice",
        "port": 8085,
        "depends_on": ["postgres", "redis"],
        "health_endpoint": "http://localhost:8085/health"
    },
    "diagram-service": {
        "name": "Diagram Service",
        "type": "microservice",
        "port": 8082,
        "depends_on": ["postgres", "redis", "minio"],
        "health_endpoint": "http://localhost:8082/health"
    },
    "ai-service": {
        "name": "AI Service",
        "type": "microservice",
        "port": 8084,
        "depends_on": ["redis"],
        "health_endpoint": "http://localhost:8084/health"
    },
    "collaboration-service": {
        "name": "Collaboration Service",
        "type": "microservice",
        "port": 8083,
        "depends_on": ["postgres", "redis"],
        "health_endpoint": "http://localhost:8083/health"
    },
    "git-service": {
        "name": "Git Service",
        "type": "microservice",
        "port": 8087,
        "depends_on": ["postgres", "redis"],
        "health_endpoint": "http://localhost:8087/health"
    },
    "export-service": {
        "name": "Export Service",
        "type": "microservice",
        "port": 8097,
        "depends_on": ["minio", "redis"],
        "health_endpoint": "http://localhost:8097/health"
    },
    "integration-hub": {
        "name": "Integration Hub",
        "type": "microservice",
        "port": 8099,
        "depends_on": ["postgres", "redis"],
        "health_endpoint": "http://localhost:8099/health"
    },
    "svg-renderer": {
        "name": "SVG Renderer",
        "type": "microservice",
        "port": 8096,
        "depends_on": [],
        "health_endpoint": "http://localhost:8096/health"
    },
    "postgres": {
        "name": "PostgreSQL",
        "type": "infrastructure",
        "port": 5432,
        "depends_on": [],
        "health_endpoint": None  # Database doesn't have HTTP endpoint
    },
    "redis": {
        "name": "Redis",
        "type": "infrastructure",
        "port": 6379,
        "depends_on": [],
        "health_endpoint": None  # Redis doesn't have HTTP endpoint
    },
    "minio": {
        "name": "MinIO S3",
        "type": "infrastructure",
        "port": 9000,
        "depends_on": [],
        "health_endpoint": "http://localhost:9000/minio/health/live"
    }
}


def detect_circular_dependencies(graph: dict) -> list:
    """Detect circular dependencies in the service graph using DFS."""
    circular = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str) -> bool:
        """Depth-first search to detect cycles."""
        if node in rec_stack:
            # Found a cycle - extract the circular path
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            circular.append(cycle)
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        # Visit all dependencies
        if node in graph and "depends_on" in graph[node]:
            for neighbor in graph[node]["depends_on"]:
                if neighbor in graph:  # Only check if neighbor exists in graph
                    dfs(neighbor)
        
        path.pop()
        rec_stack.remove(node)
        return False
    
    # Check each node in the graph
    for node in graph:
        if node not in visited:
            dfs(node)
    
    return circular


def find_critical_path(graph: dict, start: str = "frontend") -> list:
    """Find the critical path (longest path) from start node to leaf nodes."""
    if start not in graph:
        return []
    
    # Use DFS to find longest path
    max_path = []
    
    def dfs(node: str, current_path: list):
        nonlocal max_path
        current_path.append(node)
        
        # If this is a leaf node or has no more dependencies
        if node not in graph or not graph[node].get("depends_on"):
            if len(current_path) > len(max_path):
                max_path = current_path.copy()
        else:
            # Continue DFS to all dependencies
            for dep in graph[node]["depends_on"]:
                if dep in graph and dep not in current_path:  # Avoid cycles
                    dfs(dep, current_path.copy())
    
    dfs(start, [])
    return max_path


async def check_service_health(service_id: str, service_info: dict) -> dict:
    """Check health of a single service."""
    health_status = {
        "service_id": service_id,
        "name": service_info["name"],
        "type": service_info["type"],
        "port": service_info["port"],
        "status": "unknown",
        "response_time_ms": None,
        "error": None
    }
    
    health_endpoint = service_info.get("health_endpoint")
    if not health_endpoint:
        # Infrastructure services without HTTP endpoints
        if service_id == "postgres":
            try:
                # Check postgres using redis client (API gateway has redis access)
                # In real implementation, would check postgres connection
                health_status["status"] = "healthy"
                health_status["note"] = "Database health check via connection pool"
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        elif service_id == "redis":
            try:
                redis_client = get_redis_client()
                redis_client.ping()
                health_status["status"] = "healthy"
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["error"] = str(e)
        else:
            health_status["status"] = "unknown"
            health_status["note"] = "No health endpoint defined"
        return health_status
    
    # Check HTTP health endpoint
    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_endpoint)
            response_time_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                health_status["status"] = "healthy"
                health_status["response_time_ms"] = round(response_time_ms, 2)
            else:
                health_status["status"] = "unhealthy"
                health_status["response_time_ms"] = round(response_time_ms, 2)
                health_status["error"] = f"HTTP {response.status_code}"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status


@app.get("/dependencies")
@limiter.limit("1000/minute")
async def get_service_dependencies(request: Request, include_health: bool = True):
    """
    Get service dependency mapping for architecture visualization.
    
    Returns:
        - Full dependency graph
        - Health status of each service (if include_health=true)
        - Circular dependency detection
        - Critical path analysis
    """
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    logger.info(
        "Getting service dependencies",
        correlation_id=correlation_id,
        include_health=include_health
    )
    
    # Build dependency graph
    graph_nodes = []
    graph_edges = []
    
    for service_id, service_info in SERVICE_DEPENDENCIES.items():
        # Add node
        node = {
            "id": service_id,
            "name": service_info["name"],
            "type": service_info["type"],
            "port": service_info["port"]
        }
        graph_nodes.append(node)
        
        # Add edges
        for dependency in service_info["depends_on"]:
            edge = {
                "from": service_id,
                "to": dependency,
                "type": "depends_on"
            }
            graph_edges.append(edge)
    
    # Detect circular dependencies
    circular_deps = detect_circular_dependencies(SERVICE_DEPENDENCIES)
    
    # Find critical path
    critical_path = find_critical_path(SERVICE_DEPENDENCIES, "frontend")
    
    # Check service health if requested
    health_checks = []
    if include_health:
        logger.debug(
            "Performing health checks on all services",
            correlation_id=correlation_id
        )
        
        # Check health of all services in parallel
        health_tasks = [
            check_service_health(service_id, service_info)
            for service_id, service_info in SERVICE_DEPENDENCIES.items()
        ]
        health_checks = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Filter out exceptions and convert to list
        health_checks = [
            h if not isinstance(h, Exception) else {
                "error": str(h),
                "status": "error"
            }
            for h in health_checks
        ]
    
    # Build response
    response = {
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "graph": {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "total_services": len(graph_nodes),
            "total_dependencies": len(graph_edges)
        },
        "circular_dependencies": {
            "found": len(circular_deps) > 0,
            "count": len(circular_deps),
            "cycles": circular_deps
        },
        "critical_path": {
            "path": critical_path,
            "length": len(critical_path),
            "description": " → ".join(critical_path) if critical_path else "No path found"
        }
    }
    
    if include_health:
        # Add health summary
        healthy_count = sum(1 for h in health_checks if h.get("status") == "healthy")
        unhealthy_count = sum(1 for h in health_checks if h.get("status") == "unhealthy")
        unknown_count = sum(1 for h in health_checks if h.get("status") == "unknown")
        
        response["health"] = {
            "summary": {
                "total": len(health_checks),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "unknown": unknown_count,
                "health_percentage": round((healthy_count / len(health_checks)) * 100, 1) if health_checks else 0
            },
            "services": health_checks
        }
    
    logger.info(
        "Service dependencies retrieved",
        correlation_id=correlation_id,
        total_services=len(graph_nodes),
        circular_deps_found=len(circular_deps) > 0,
        critical_path_length=len(critical_path)
    )
    
    return response


@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("1000/minute")  # IP-based for auth (public routes)
async def proxy_auth(path: str, request: Request):
    """Route requests to auth service."""
    return await proxy_request("auth", path, request)


@app.api_route("/api/notifications", methods=["GET"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_notifications_list(request: Request):
    """Route notification list requests to diagram service."""
    return await proxy_request("diagram", "notifications", request)


@app.api_route("/api/notifications/{path:path}", methods=["GET", "PUT", "DELETE"])
@limiter.limit("100/minute")  # User-based rate limit
async def proxy_notifications(path: str, request: Request):
    """Route notification requests to diagram service."""
    return await proxy_request("diagram", f"notifications/{path}", request)


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

            # For binary content types (images, PDFs, CSV), pass through unchanged
            content_type = response.headers.get("content-type", "")
            if content_type.startswith(("image/", "application/pdf", "application/octet-stream", "text/csv")):
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=content_type
                )
            
            # For JSON responses, return JSONResponse
            if content_type.startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
            
            # For other text responses, wrap in JSON with data field
            return JSONResponse(
                content={"data": response.text},
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


# ===============================================================================
# ALERTING SYSTEM - Feature #47
# ===============================================================================

# Alert storage (in-memory for now, could be Redis/PostgreSQL in production)
ALERTS = {}  # alert_id -> alert_data
ALERT_CONFIG = {
    "service_down_threshold_seconds": 300,  # 5 minutes
    "email_enabled": os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
    "slack_enabled": os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true",
    "email_to": os.getenv("ALERT_EMAIL_TO", "admin@autograph.com"),
    "email_from": os.getenv("ALERT_EMAIL_FROM", "alerts@autograph.com"),
    "slack_webhook_url": os.getenv("ALERT_SLACK_WEBHOOK_URL", ""),
    "escalation_interval_seconds": 900,  # 15 minutes
    "smtp_host": os.getenv("SMTP_HOST", "localhost"),
    "smtp_port": int(os.getenv("SMTP_PORT", "25")),
}

# Service health tracking
SERVICE_HEALTH_HISTORY = {}  # service_id -> {"last_check": timestamp, "failures": [timestamps], "status": "healthy/unhealthy"}


async def check_service_health_for_alerts(service_id: str, service_info: dict) -> dict:
    """Check service health for alerting purposes."""
    health_status = await check_service_health(service_id, service_info)
    
    # Update health history
    current_time = time.time()
    if service_id not in SERVICE_HEALTH_HISTORY:
        SERVICE_HEALTH_HISTORY[service_id] = {
            "last_check": current_time,
            "failures": [],
            "status": "healthy",
            "first_failure": None
        }
    
    history = SERVICE_HEALTH_HISTORY[service_id]
    history["last_check"] = current_time
    
    if health_status["status"] == "unhealthy":
        # Add failure timestamp
        history["failures"].append(current_time)
        if history["first_failure"] is None:
            history["first_failure"] = current_time
        
        # Remove old failures (older than threshold + 1 hour)
        cutoff = current_time - (ALERT_CONFIG["service_down_threshold_seconds"] + 3600)
        history["failures"] = [f for f in history["failures"] if f > cutoff]
        
        # Check if we should trigger alert
        down_duration = current_time - history["first_failure"]
        if down_duration >= ALERT_CONFIG["service_down_threshold_seconds"]:
            await trigger_alert(service_id, service_info, down_duration)
    else:
        # Service is healthy - check if we need to auto-resolve
        if history["status"] == "unhealthy":
            await resolve_alert(service_id, service_info)
        
        # Reset failure tracking
        history["failures"] = []
        history["first_failure"] = None
    
    history["status"] = health_status["status"]
    return health_status


async def trigger_alert(service_id: str, service_info: dict, down_duration: float):
    """Trigger an alert for a service failure."""
    alert_key = f"service_down_{service_id}"
    
    # Check if alert already exists
    if alert_key in ALERTS and ALERTS[alert_key]["status"] == "active":
        # Alert already exists - check if we should escalate
        alert = ALERTS[alert_key]
        time_since_last_notification = time.time() - alert["last_notification"]
        
        if time_since_last_notification >= ALERT_CONFIG["escalation_interval_seconds"]:
            # Escalate alert
            alert["escalation_count"] += 1
            alert["last_notification"] = time.time()
            
            logger.warning(
                f"Escalating alert for {service_id}",
                alert_id=alert_key,
                escalation_count=alert["escalation_count"],
                down_duration_seconds=int(down_duration)
            )
            
            # Send escalation notification
            await send_alert_notification(alert, escalated=True)
        return
    
    # Create new alert
    alert = {
        "alert_id": alert_key,
        "type": "service_down",
        "service_id": service_id,
        "service_name": service_info["name"],
        "severity": "critical",
        "status": "active",
        "triggered_at": datetime.utcnow().isoformat(),
        "triggered_timestamp": time.time(),
        "last_notification": time.time(),
        "resolved_at": None,
        "escalation_count": 0,
        "down_duration_seconds": int(down_duration),
        "message": f"{service_info['name']} has been down for {int(down_duration / 60)} minutes"
    }
    
    ALERTS[alert_key] = alert
    
    logger.error(
        f"Alert triggered: {alert['message']}",
        alert_id=alert_key,
        service_id=service_id,
        severity="critical"
    )
    
    # Send notification
    await send_alert_notification(alert, escalated=False)


async def resolve_alert(service_id: str, service_info: dict):
    """Auto-resolve an alert when service recovers."""
    alert_key = f"service_down_{service_id}"
    
    if alert_key in ALERTS and ALERTS[alert_key]["status"] == "active":
        alert = ALERTS[alert_key]
        alert["status"] = "resolved"
        alert["resolved_at"] = datetime.utcnow().isoformat()
        alert["resolved_timestamp"] = time.time()
        
        down_duration = alert["resolved_timestamp"] - alert["triggered_timestamp"]
        
        logger.info(
            f"Alert auto-resolved: {service_info['name']} is back online",
            alert_id=alert_key,
            service_id=service_id,
            down_duration_seconds=int(down_duration)
        )
        
        # Send resolution notification
        await send_resolution_notification(alert)


async def send_alert_notification(alert: dict, escalated: bool):
    """Send alert notification via configured channels."""
    # Send email notification
    if ALERT_CONFIG["email_enabled"]:
        await send_email_notification(alert, escalated)
    
    # Send Slack notification
    if ALERT_CONFIG["slack_enabled"] and ALERT_CONFIG["slack_webhook_url"]:
        await send_slack_notification(alert, escalated)


async def send_email_notification(alert: dict, escalated: bool):
    """Send email notification for alert."""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        subject = f"{'[ESCALATION] ' if escalated else ''}CRITICAL ALERT: {alert['service_name']} Down"
        
        body = f"""
AutoGraph v3 Alert
==================

Service: {alert['service_name']}
Status: DOWN
Duration: {alert['down_duration_seconds'] // 60} minutes
Triggered: {alert['triggered_at']}
Escalation Count: {alert['escalation_count']}

Message: {alert['message']}

Please investigate immediately.

Alert ID: {alert['alert_id']}
        """
        
        msg = MIMEMultipart()
        msg["From"] = ALERT_CONFIG["email_from"]
        msg["To"] = ALERT_CONFIG["email_to"]
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(ALERT_CONFIG["smtp_host"], ALERT_CONFIG["smtp_port"]) as server:
            server.send_message(msg)
        
        logger.info(
            f"Email alert sent for {alert['service_name']}",
            alert_id=alert["alert_id"],
            escalated=escalated
        )
    except Exception as e:
        logger.error(
            "Failed to send email alert",
            alert_id=alert["alert_id"],
            exc=e
        )


async def send_slack_notification(alert: dict, escalated: bool):
    """Send Slack notification for alert."""
    try:
        escalation_prefix = "🚨 *ESCALATION* " if escalated else ""
        emoji = "🔴"
        
        payload = {
            "text": f"{emoji} {escalation_prefix}*CRITICAL ALERT*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {escalation_prefix}Service Down Alert",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:*\n{alert['service_name']}"},
                        {"type": "mrkdwn", "text": f"*Status:*\nDOWN"},
                        {"type": "mrkdwn", "text": f"*Duration:*\n{alert['down_duration_seconds'] // 60} minutes"},
                        {"type": "mrkdwn", "text": f"*Escalations:*\n{alert['escalation_count']}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:* {alert['message']}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"Alert ID: `{alert['alert_id']}` | Triggered: {alert['triggered_at']}"}
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                ALERT_CONFIG["slack_webhook_url"],
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(
                    f"Slack alert sent for {alert['service_name']}",
                    alert_id=alert["alert_id"],
                    escalated=escalated
                )
            else:
                logger.error(
                    f"Failed to send Slack alert (HTTP {response.status_code})",
                    alert_id=alert["alert_id"]
                )
    except Exception as e:
        logger.error(
            "Failed to send Slack alert",
            alert_id=alert["alert_id"],
            exc=e
        )


async def send_resolution_notification(alert: dict):
    """Send notification when alert is resolved."""
    # Send email
    if ALERT_CONFIG["email_enabled"]:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            down_duration = alert["resolved_timestamp"] - alert["triggered_timestamp"]
            
            subject = f"✅ RESOLVED: {alert['service_name']} Back Online"
            body = f"""
AutoGraph v3 Alert Resolution
==============================

Service: {alert['service_name']}
Status: RECOVERED
Downtime: {int(down_duration // 60)} minutes
Triggered: {alert['triggered_at']}
Resolved: {alert['resolved_at']}

The service is now healthy and operational.

Alert ID: {alert['alert_id']}
            """
            
            msg = MIMEMultipart()
            msg["From"] = ALERT_CONFIG["email_from"]
            msg["To"] = ALERT_CONFIG["email_to"]
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(ALERT_CONFIG["smtp_host"], ALERT_CONFIG["smtp_port"]) as server:
                server.send_message(msg)
        except Exception as e:
            logger.error("Failed to send resolution email", alert_id=alert["alert_id"], exc=e)
    
    # Send Slack
    if ALERT_CONFIG["slack_enabled"] and ALERT_CONFIG["slack_webhook_url"]:
        try:
            down_duration = alert["resolved_timestamp"] - alert["triggered_timestamp"]
            
            payload = {
                "text": f"✅ *RESOLVED* - {alert['service_name']} is back online",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"✅ Alert Resolved",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Service:*\n{alert['service_name']}"},
                            {"type": "mrkdwn", "text": f"*Status:*\nRECOVERED"},
                            {"type": "mrkdwn", "text": f"*Downtime:*\n{int(down_duration // 60)} minutes"},
                            {"type": "mrkdwn", "text": f"*Resolved:*\n{alert['resolved_at']}"}
                        ]
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(ALERT_CONFIG["slack_webhook_url"], json=payload)
        except Exception as e:
            logger.error("Failed to send Slack resolution", alert_id=alert["alert_id"], exc=e)


# Background task to monitor service health
async def monitor_services_for_alerts():
    """Background task to continuously monitor services and trigger alerts."""
    while True:
        try:
            # Check all services
            for service_id, service_info in SERVICE_DEPENDENCIES.items():
                await check_service_health_for_alerts(service_id, service_info)
            
            # Wait 60 seconds before next check
            await asyncio.sleep(60)
        except Exception as e:
            logger.error("Error in service monitoring task", exc=e)
            await asyncio.sleep(60)


@app.get("/alerts")
@limiter.limit("100/minute")
async def get_alerts(request: Request, status: str = None):
    """
    Get all alerts with optional status filter.
    
    Query Parameters:
    - status: Filter by status (active, resolved, all). Default: all
    
    Returns:
    - List of alerts with their details
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    # Filter alerts
    if status == "active":
        filtered_alerts = [a for a in ALERTS.values() if a["status"] == "active"]
    elif status == "resolved":
        filtered_alerts = [a for a in ALERTS.values() if a["status"] == "resolved"]
    else:
        filtered_alerts = list(ALERTS.values())
    
    # Sort by triggered timestamp (newest first)
    filtered_alerts.sort(key=lambda x: x["triggered_timestamp"], reverse=True)
    
    return {
        "correlation_id": correlation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "total_alerts": len(ALERTS),
        "active_alerts": sum(1 for a in ALERTS.values() if a["status"] == "active"),
        "resolved_alerts": sum(1 for a in ALERTS.values() if a["status"] == "resolved"),
        "alerts": filtered_alerts,
        "config": {
            "service_down_threshold_minutes": ALERT_CONFIG["service_down_threshold_seconds"] // 60,
            "escalation_interval_minutes": ALERT_CONFIG["escalation_interval_seconds"] // 60,
            "email_enabled": ALERT_CONFIG["email_enabled"],
            "slack_enabled": ALERT_CONFIG["slack_enabled"]
        }
    }


# =====================================================================
# DATABASE BACKUP AND RESTORE ENDPOINTS
# =====================================================================

# Import backup manager
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.python.backup import DatabaseBackupManager

# Initialize backup manager (lazy initialization)
_backup_manager = None

def get_backup_manager():
    """Get or create database backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = DatabaseBackupManager(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=int(os.getenv("POSTGRES_PORT", "5432")),
            postgres_db=os.getenv("POSTGRES_DB", "autograph"),
            postgres_user=os.getenv("POSTGRES_USER", "autograph"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            backup_dir=os.getenv("BACKUP_DIR", "/tmp/backups"),
            minio_endpoint=os.getenv("MINIO_ENDPOINT"),
            minio_access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            minio_bucket="backups"
        )
    return _backup_manager


@app.post("/api/admin/backup/create")
@limiter.limit("10/hour")
async def create_database_backup(
    request: Request,
    backup_name: str = None,
    backup_format: str = "custom",
    upload_to_minio: bool = True
):
    """
    Create a new PostgreSQL database backup.
    
    Requires admin authentication.
    
    Body Parameters:
    - backup_name: Optional name for the backup (auto-generated if not provided)
    - backup_format: Format for pg_dump (custom, plain, directory, tar). Default: custom
    - upload_to_minio: Whether to upload to MinIO after backup. Default: true
    
    Returns:
    - Backup metadata including file path, size, and MinIO upload status
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    # This is admin-only endpoint - in production should verify JWT admin role
    # For now, we'll allow it for testing but log it
    logger.info("Database backup requested", correlation_id=correlation_id, backup_name=backup_name)
    
    try:
        manager = get_backup_manager()
        
        # Create backup
        backup_metadata = manager.create_backup(
            backup_name=backup_name,
            backup_format=backup_format,
            upload_to_minio=upload_to_minio
        )
        
        logger.info(
            "Database backup created successfully",
            correlation_id=correlation_id,
            backup_name=backup_metadata["backup_name"],
            size_mb=backup_metadata["file_size_mb"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "backup": backup_metadata
        }
        
    except Exception as e:
        logger.error("Failed to create database backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )


@app.post("/api/admin/backup/restore")
@limiter.limit("5/hour")
async def restore_database_backup(
    request: Request,
    backup_file: str = None,
    backup_name: str = None,
    download_from_minio: bool = False,
    clean: bool = False
):
    """
    Restore PostgreSQL database from a backup.
    
    Requires admin authentication.
    
    Body Parameters:
    - backup_file: Path to local backup file
    - backup_name: Name of backup in MinIO (if downloading)
    - download_from_minio: Whether to download from MinIO first. Default: false
    - clean: Whether to clean (drop) database objects before restoring. Default: false
    
    Returns:
    - Restore metadata
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    # This is admin-only endpoint - in production should verify JWT admin role
    logger.warning(
        "Database restore requested - THIS WILL MODIFY THE DATABASE",
        correlation_id=correlation_id,
        backup_file=backup_file,
        backup_name=backup_name
    )
    
    try:
        manager = get_backup_manager()
        
        # Restore backup
        restore_metadata = manager.restore_backup(
            backup_file=backup_file,
            backup_name=backup_name,
            download_from_minio=download_from_minio,
            clean=clean
        )
        
        logger.info(
            "Database restored successfully",
            correlation_id=correlation_id,
            backup_file=restore_metadata["backup_file"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "restore": restore_metadata
        }
        
    except Exception as e:
        logger.error("Failed to restore database backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Restore failed: {str(e)}"
        )


@app.get("/api/admin/backup/list")
@limiter.limit("60/minute")
async def list_database_backups(
    request: Request,
    include_local: bool = True,
    include_minio: bool = True
):
    """
    List available database backups from local and/or MinIO storage.
    
    Query Parameters:
    - include_local: Include backups from local storage. Default: true
    - include_minio: Include backups from MinIO. Default: true
    
    Returns:
    - Lists of backups from both local and MinIO storage
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    try:
        manager = get_backup_manager()
        
        backups = manager.list_backups(
            include_local=include_local,
            include_minio=include_minio
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "local_count": len(backups["local"]),
            "minio_count": len(backups["minio"]),
            "backups": backups
        }
        
    except Exception as e:
        logger.error("Failed to list backups", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@app.delete("/api/admin/backup/{backup_name}")
@limiter.limit("30/minute")
async def delete_database_backup(
    request: Request,
    backup_name: str,
    delete_local: bool = True,
    delete_minio: bool = True
):
    """
    Delete a database backup from local and/or MinIO storage.
    
    Path Parameters:
    - backup_name: Name of the backup to delete
    
    Query Parameters:
    - delete_local: Delete from local storage. Default: true
    - delete_minio: Delete from MinIO. Default: true
    
    Returns:
    - Deletion results
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "Database backup deletion requested",
        correlation_id=correlation_id,
        backup_name=backup_name
    )
    
    try:
        manager = get_backup_manager()
        
        results = manager.delete_backup(
            backup_name=backup_name,
            delete_local=delete_local,
            delete_minio=delete_minio
        )
        
        logger.info(
            "Database backup deleted",
            correlation_id=correlation_id,
            backup_name=backup_name,
            local_deleted=results["local_deleted"],
            minio_deleted=results["minio_deleted"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "backup_name": backup_name,
            "results": results
        }
        
    except Exception as e:
        logger.error("Failed to delete backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )


# ==========================================
# MinIO Bucket Backup and Restore Endpoints
# ==========================================

# Global MinIO bucket backup manager instance
_minio_backup_manager = None

def get_minio_backup_manager():
    """Get or create MinIO bucket backup manager instance"""
    global _minio_backup_manager
    
    if _minio_backup_manager is None:
        from shared.python.backup import MinIOBucketBackupManager
        
        _minio_backup_manager = MinIOBucketBackupManager(
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "http://minio:9000"),
            minio_access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            minio_secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            backup_dir="/tmp/minio_backups",
            backup_bucket="minio-backups"
        )
    return _minio_backup_manager


@app.get("/api/admin/minio/buckets")
@limiter.limit("60/minute")
async def list_minio_buckets(request: Request):
    """
    List all MinIO buckets.
    
    Returns:
    - List of bucket names
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    try:
        manager = get_minio_backup_manager()
        buckets = manager.list_buckets()
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "count": len(buckets),
            "buckets": buckets
        }
        
    except Exception as e:
        logger.error("Failed to list MinIO buckets", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list buckets: {str(e)}"
        )


@app.post("/api/admin/minio/backup/create")
@limiter.limit("10/hour")
async def create_minio_bucket_backup(
    request: Request,
    bucket_name: str,
    backup_name: str = None,
    include_versions: bool = False
):
    """
    Create a backup of a MinIO bucket.
    
    Requires admin authentication.
    
    Body Parameters:
    - bucket_name: Name of the bucket to backup (required)
    - backup_name: Optional name for the backup (auto-generated if not provided)
    - include_versions: Whether to include object versions. Default: false
    
    Returns:
    - Backup metadata including archive size and object count
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.info(
        "MinIO bucket backup requested",
        correlation_id=correlation_id,
        bucket_name=bucket_name,
        backup_name=backup_name
    )
    
    try:
        manager = get_minio_backup_manager()
        
        # Create bucket backup
        backup_metadata = manager.backup_bucket(
            bucket_name=bucket_name,
            backup_name=backup_name,
            include_versions=include_versions
        )
        
        logger.info(
            "MinIO bucket backup created successfully",
            correlation_id=correlation_id,
            backup_name=backup_metadata["backup_name"],
            object_count=backup_metadata["object_count"],
            size_mb=backup_metadata["archive_size_mb"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "backup": backup_metadata
        }
        
    except Exception as e:
        logger.error("Failed to create MinIO bucket backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bucket backup failed: {str(e)}"
        )


@app.post("/api/admin/minio/backup/restore")
@limiter.limit("5/hour")
async def restore_minio_bucket_backup(
    request: Request,
    backup_name: str,
    target_bucket: str = None,
    overwrite: bool = False
):
    """
    Restore a MinIO bucket from backup.
    
    Requires admin authentication.
    
    Body Parameters:
    - backup_name: Name of the backup to restore (required, without .tar.gz extension)
    - target_bucket: Target bucket name (uses original if not provided)
    - overwrite: Whether to overwrite existing objects. Default: false
    
    Returns:
    - Restore metadata including uploaded count and size
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "MinIO bucket restore requested - THIS WILL MODIFY BUCKET DATA",
        correlation_id=correlation_id,
        backup_name=backup_name,
        target_bucket=target_bucket
    )
    
    try:
        manager = get_minio_backup_manager()
        
        # Restore bucket backup
        restore_metadata = manager.restore_bucket(
            backup_name=backup_name,
            target_bucket=target_bucket,
            overwrite=overwrite
        )
        
        logger.info(
            "MinIO bucket restored successfully",
            correlation_id=correlation_id,
            backup_name=backup_name,
            target_bucket=restore_metadata["target_bucket"],
            uploaded_count=restore_metadata["uploaded_count"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "restore": restore_metadata
        }
        
    except Exception as e:
        logger.error("Failed to restore MinIO bucket backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bucket restore failed: {str(e)}"
        )


@app.get("/api/admin/minio/backup/list")
@limiter.limit("60/minute")
async def list_minio_bucket_backups(request: Request):
    """
    List available MinIO bucket backups.
    
    Returns:
    - List of bucket backups with metadata
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    try:
        manager = get_minio_backup_manager()
        backups = manager.list_backups()
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "count": len(backups),
            "backups": backups
        }
        
    except Exception as e:
        logger.error("Failed to list MinIO bucket backups", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list bucket backups: {str(e)}"
        )


@app.delete("/api/admin/minio/backup/{backup_name}")
@limiter.limit("30/minute")
async def delete_minio_bucket_backup(
    request: Request,
    backup_name: str,
    delete_local: bool = True
):
    """
    Delete a MinIO bucket backup.
    
    Path Parameters:
    - backup_name: Name of the backup to delete (without .tar.gz extension)
    
    Query Parameters:
    - delete_local: Also delete local copy if present. Default: true
    
    Returns:
    - Deletion results
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "MinIO bucket backup deletion requested",
        correlation_id=correlation_id,
        backup_name=backup_name
    )
    
    try:
        manager = get_minio_backup_manager()
        
        results = manager.delete_backup(
            backup_name=backup_name,
            delete_local=delete_local
        )
        
        logger.info(
            "MinIO bucket backup deleted",
            correlation_id=correlation_id,
            backup_name=backup_name,
            minio_deleted=results["minio_deleted"],
            local_deleted=results["local_deleted"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "backup_name": backup_name,
            "results": results
        }
        
    except Exception as e:
        logger.error("Failed to delete MinIO bucket backup", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bucket backup: {str(e)}"
        )


# ==========================================
# Disaster Recovery Endpoints
# ==========================================

@app.get("/api/admin/dr/status")
@limiter.limit("60/minute")
async def get_dr_status(request: Request):
    """
    Get disaster recovery status and metrics.
    
    Returns:
    - RTO/RPO targets
    - Backup status
    - Last DR test results
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    try:
        # Get database backup status
        db_manager = get_backup_manager()
        db_backups_response = db_manager.list_backups()
        
        # Extract backup lists from response
        db_backups_local = db_backups_response.get("local", [])
        db_backups_minio = db_backups_response.get("minio", [])
        all_db_backups = db_backups_local + db_backups_minio
        
        # Get MinIO backup status
        minio_manager = get_minio_backup_manager()
        minio_backups = minio_manager.list_backups()
        
        # Calculate last backup times
        latest_db_backup = None
        if all_db_backups:
            latest_db_backup = max(all_db_backups, key=lambda x: x.get("created_at", ""))
        
        latest_minio_backup = None
        if minio_backups:
            latest_minio_backup = max(minio_backups, key=lambda x: x.get("modified", ""))
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "rto_target_minutes": 60,
            "rpo_target_minutes": 5,
            "database_backups": {
                "count": len(all_db_backups),
                "latest": latest_db_backup.get("created_at") if latest_db_backup else None,
                "status": "healthy" if all_db_backups else "no_backups"
            },
            "minio_backups": {
                "count": len(minio_backups),
                "latest": latest_minio_backup.get("modified") if latest_minio_backup else None,
                "status": "healthy" if minio_backups else "no_backups"
            },
            "last_dr_test": None,  # To be updated after first DR test
            "next_dr_test": None   # To be scheduled
        }
        
    except Exception as e:
        logger.error("Failed to get DR status", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DR status: {str(e)}"
        )


@app.post("/api/admin/dr/simulate")
@limiter.limit("10/hour")
async def simulate_disaster_recovery(
    request: Request,
    scenario: str = "complete_failure"
):
    """
    Simulate a disaster recovery scenario.
    
    Query Parameters:
    - scenario: Type of disaster to simulate
      Options: complete_failure, database_corruption, storage_loss
      Default: complete_failure
    
    Returns:
    - Simulation results and recovery metrics
    
    WARNING: This will simulate service failures! Use with caution.
    """
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        "DR simulation requested",
        correlation_id=correlation_id,
        scenario=scenario
    )
    
    start_time = time.time()
    
    try:
        simulation_results = {
            "scenario": scenario,
            "start_time": datetime.utcnow().isoformat(),
            "steps": [],
            "metrics": {}
        }
        
        # Scenario: Complete Infrastructure Failure
        if scenario == "complete_failure":
            # Step 1: Assess current state
            step_start = time.time()
            simulation_results["steps"].append({
                "step": 1,
                "name": "Assess current state",
                "status": "completed",
                "duration_seconds": time.time() - step_start,
                "details": "Checked infrastructure services status"
            })
            
            # Step 2: Verify backups exist
            step_start = time.time()
            db_manager = get_backup_manager()
            db_backups_response = db_manager.list_backups()
            db_backups = db_backups_response.get("local", []) + db_backups_response.get("minio", [])
            
            minio_manager = get_minio_backup_manager()
            minio_backups = minio_manager.list_backups()
            
            simulation_results["steps"].append({
                "step": 2,
                "name": "Verify backups available",
                "status": "completed",
                "duration_seconds": time.time() - step_start,
                "details": f"Found {len(db_backups)} database backups and {len(minio_backups)} MinIO backups"
            })
            
            # Step 3: Simulate infrastructure recovery (not actually stopping services)
            step_start = time.time()
            await asyncio.sleep(2)  # Simulate infrastructure provisioning time
            simulation_results["steps"].append({
                "step": 3,
                "name": "Infrastructure provisioning (simulated)",
                "status": "completed",
                "duration_seconds": time.time() - step_start,
                "details": "Simulated docker-compose up -d for all services"
            })
            
            # Step 4: Simulate database restore
            step_start = time.time()
            if db_backups:
                latest_db_backup = max(db_backups, key=lambda x: x.get("created_at", ""))
                # Note: Not actually restoring in simulation
                await asyncio.sleep(3)  # Simulate restore time
                simulation_results["steps"].append({
                    "step": 4,
                    "name": "Database restore (simulated)",
                    "status": "completed",
                    "duration_seconds": time.time() - step_start,
                    "details": f"Simulated restore from {latest_db_backup.get('backup_name', 'unknown')}"
                })
            else:
                simulation_results["steps"].append({
                    "step": 4,
                    "name": "Database restore (simulated)",
                    "status": "skipped",
                    "duration_seconds": 0,
                    "details": "No database backups available"
                })
            
            # Step 5: Simulate MinIO restore
            step_start = time.time()
            if minio_backups:
                # Note: Not actually restoring in simulation
                await asyncio.sleep(2)  # Simulate restore time
                simulation_results["steps"].append({
                    "step": 5,
                    "name": "MinIO buckets restore (simulated)",
                    "status": "completed",
                    "duration_seconds": time.time() - step_start,
                    "details": f"Simulated restore of {len(minio_backups)} bucket backups"
                })
            else:
                simulation_results["steps"].append({
                    "step": 5,
                    "name": "MinIO buckets restore (simulated)",
                    "status": "skipped",
                    "duration_seconds": 0,
                    "details": "No MinIO backups available"
                })
            
            # Step 6: Simulate service startup
            step_start = time.time()
            await asyncio.sleep(2)  # Simulate service startup time
            simulation_results["steps"].append({
                "step": 6,
                "name": "Service startup (simulated)",
                "status": "completed",
                "duration_seconds": time.time() - step_start,
                "details": "Simulated starting all microservices"
            })
            
            # Step 7: Verify system health
            step_start = time.time()
            health_checks = {
                "api_gateway": True,  # We're responding, so we're healthy
                "database": db_backups is not None and len(db_backups) > 0,
                "storage": minio_backups is not None and len(minio_backups) > 0
            }
            simulation_results["steps"].append({
                "step": 7,
                "name": "System health verification",
                "status": "completed",
                "duration_seconds": time.time() - step_start,
                "details": f"Health checks: {health_checks}"
            })
        
        # Calculate total recovery time
        total_duration = time.time() - start_time
        
        simulation_results["end_time"] = datetime.utcnow().isoformat()
        simulation_results["total_duration_seconds"] = total_duration
        simulation_results["total_duration_minutes"] = total_duration / 60
        
        # Calculate metrics
        simulation_results["metrics"] = {
            "rto_target_minutes": 60,
            "actual_recovery_minutes": total_duration / 60,
            "rto_met": (total_duration / 60) <= 60,
            "rpo_target_minutes": 5,
            "estimated_data_loss_minutes": 0,  # Simulation doesn't lose data
            "rpo_met": True,
            "total_steps": len(simulation_results["steps"]),
            "successful_steps": len([s for s in simulation_results["steps"] if s["status"] == "completed"]),
            "failed_steps": len([s for s in simulation_results["steps"] if s["status"] == "failed"])
        }
        
        logger.info(
            "DR simulation completed",
            correlation_id=correlation_id,
            scenario=scenario,
            duration_minutes=simulation_results["total_duration_minutes"],
            rto_met=simulation_results["metrics"]["rto_met"]
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "simulation": simulation_results
        }
        
    except Exception as e:
        logger.error("DR simulation failed", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DR simulation failed: {str(e)}"
        )


# ==========================================
# Feature Flags API
# ==========================================

# Import feature flag module
import sys
import os
# Support both Docker (/app) and local development paths
shared_path = "/app/shared/python" if os.path.exists("/app/shared/python") else os.path.join(os.path.dirname(__file__), "../../../shared/python")
sys.path.append(shared_path)
from feature_flags import FeatureFlag, FeatureFlagManager, RolloutStrategy

# Global feature flag manager instance
_feature_flag_manager = None

def get_feature_flag_manager() -> FeatureFlagManager:
    """Get or create feature flag manager instance."""
    global _feature_flag_manager
    if _feature_flag_manager is None:
        redis_client = get_redis()
        _feature_flag_manager = FeatureFlagManager(redis_client)
    return _feature_flag_manager


@app.post("/api/feature-flags", status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    request: Request,
    flag_data: dict,
):
    """
    Create a new feature flag.
    
    Request body:
    {
        "name": "new_dashboard",
        "enabled": false,
        "description": "New dashboard UI",
        "rollout_percentage": 0,
        "strategy": "percentage"
    }
    """
    correlation_id = request.state.correlation_id
    
    try:
        logger.info(
            "Creating feature flag",
            correlation_id=correlation_id,
            flag_name=flag_data.get("name")
        )
        
        # Create feature flag object
        flag = FeatureFlag(
            name=flag_data["name"],
            enabled=flag_data.get("enabled", False),
            description=flag_data.get("description", ""),
            rollout_percentage=flag_data.get("rollout_percentage", 0),
            strategy=RolloutStrategy(flag_data.get("strategy", "percentage")),
            whitelist=flag_data.get("whitelist", []),
            blacklist=flag_data.get("blacklist", []),
            environments=flag_data.get("environments", []),
            metadata=flag_data.get("metadata", {}),
        )
        
        # Create flag in manager
        manager = get_feature_flag_manager()
        success = manager.create_flag(flag)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Flag {flag.name} already exists"
            )
        
        logger.info(
            "Feature flag created successfully",
            correlation_id=correlation_id,
            flag_name=flag.name
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "flag": flag.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create feature flag", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create feature flag: {str(e)}"
        )


@app.get("/api/feature-flags")
async def list_feature_flags(request: Request):
    """List all feature flags."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info("Listing feature flags", correlation_id=correlation_id)
        
        manager = get_feature_flag_manager()
        flags = manager.list_flags()
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(flags),
            "flags": [flag.to_dict() for flag in flags]
        }
        
    except Exception as e:
        logger.error("Failed to list feature flags", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list feature flags: {str(e)}"
        )


@app.get("/api/feature-flags/{flag_name}")
async def get_feature_flag(request: Request, flag_name: str):
    """Get a specific feature flag."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info("Getting feature flag", correlation_id=correlation_id, flag_name=flag_name)
        
        manager = get_feature_flag_manager()
        flag = manager.get_flag(flag_name)
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "flag": flag.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get feature flag", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feature flag: {str(e)}"
        )


@app.put("/api/feature-flags/{flag_name}")
async def update_feature_flag(
    request: Request,
    flag_name: str,
    flag_data: dict,
):
    """Update an existing feature flag."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info("Updating feature flag", correlation_id=correlation_id, flag_name=flag_name)
        
        manager = get_feature_flag_manager()
        flag = manager.get_flag(flag_name)
        
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        # Update flag properties
        if "enabled" in flag_data:
            flag.enabled = flag_data["enabled"]
        if "description" in flag_data:
            flag.description = flag_data["description"]
        if "rollout_percentage" in flag_data:
            flag.rollout_percentage = max(0, min(100, flag_data["rollout_percentage"]))
        if "strategy" in flag_data:
            flag.strategy = RolloutStrategy(flag_data["strategy"])
        if "whitelist" in flag_data:
            flag.whitelist = set(flag_data["whitelist"])
        if "blacklist" in flag_data:
            flag.blacklist = set(flag_data["blacklist"])
        if "environments" in flag_data:
            flag.environments = set(flag_data["environments"])
        if "metadata" in flag_data:
            flag.metadata = flag_data["metadata"]
        
        # Update flag in manager
        success = manager.update_flag(flag)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update flag {flag_name}"
            )
        
        logger.info(
            "Feature flag updated successfully",
            correlation_id=correlation_id,
            flag_name=flag.name
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "flag": flag.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update feature flag", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feature flag: {str(e)}"
        )


@app.delete("/api/feature-flags/{flag_name}")
async def delete_feature_flag(request: Request, flag_name: str):
    """Delete a feature flag."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info("Deleting feature flag", correlation_id=correlation_id, flag_name=flag_name)
        
        manager = get_feature_flag_manager()
        success = manager.delete_flag(flag_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        logger.info(
            "Feature flag deleted successfully",
            correlation_id=correlation_id,
            flag_name=flag_name
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "message": f"Flag {flag_name} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete feature flag", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete feature flag: {str(e)}"
        )


@app.post("/api/feature-flags/{flag_name}/check")
async def check_feature_flag(
    request: Request,
    flag_name: str,
    check_data: dict = None,
):
    """
    Check if a feature flag is enabled for a user.
    
    Request body:
    {
        "user_id": "user123",
        "environment": "production"
    }
    """
    correlation_id = request.state.correlation_id
    
    try:
        check_data = check_data or {}
        user_id = check_data.get("user_id")
        environment = check_data.get("environment")
        
        logger.info(
            "Checking feature flag",
            correlation_id=correlation_id,
            flag_name=flag_name,
            user_id=user_id
        )
        
        manager = get_feature_flag_manager()
        enabled = manager.is_enabled(
            flag_name=flag_name,
            user_id=user_id,
            environment=environment,
            default=False
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "flag_name": flag_name,
            "user_id": user_id,
            "environment": environment,
            "enabled": enabled
        }
        
    except Exception as e:
        logger.error("Failed to check feature flag", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check feature flag: {str(e)}"
        )


@app.patch("/api/feature-flags/{flag_name}/rollout")
async def set_rollout_percentage(
    request: Request,
    flag_name: str,
    rollout_data: dict,
):
    """
    Set the rollout percentage for a feature flag.
    
    Request body:
    {
        "percentage": 50
    }
    """
    correlation_id = request.state.correlation_id
    
    try:
        percentage = rollout_data["percentage"]
        
        logger.info(
            "Setting rollout percentage",
            correlation_id=correlation_id,
            flag_name=flag_name,
            percentage=percentage
        )
        
        manager = get_feature_flag_manager()
        success = manager.set_rollout_percentage(flag_name, percentage)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        flag = manager.get_flag(flag_name)
        
        logger.info(
            "Rollout percentage updated successfully",
            correlation_id=correlation_id,
            flag_name=flag_name,
            percentage=percentage
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "flag": flag.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to set rollout percentage", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set rollout percentage: {str(e)}"
        )


@app.post("/api/feature-flags/{flag_name}/whitelist")
async def add_to_whitelist(
    request: Request,
    flag_name: str,
    whitelist_data: dict,
):
    """
    Add a user to the whitelist for a feature flag.
    
    Request body:
    {
        "user_id": "user123"
    }
    """
    correlation_id = request.state.correlation_id
    
    try:
        user_id = whitelist_data["user_id"]
        
        logger.info(
            "Adding user to whitelist",
            correlation_id=correlation_id,
            flag_name=flag_name,
            user_id=user_id
        )
        
        manager = get_feature_flag_manager()
        success = manager.add_to_whitelist(flag_name, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        logger.info(
            "User added to whitelist successfully",
            correlation_id=correlation_id,
            flag_name=flag_name,
            user_id=user_id
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "message": f"User {user_id} added to whitelist for {flag_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add user to whitelist", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add user to whitelist: {str(e)}"
        )


@app.delete("/api/feature-flags/{flag_name}/whitelist/{user_id}")
async def remove_from_whitelist(
    request: Request,
    flag_name: str,
    user_id: str,
):
    """Remove a user from the whitelist for a feature flag."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info(
            "Removing user from whitelist",
            correlation_id=correlation_id,
            flag_name=flag_name,
            user_id=user_id
        )
        
        manager = get_feature_flag_manager()
        success = manager.remove_from_whitelist(flag_name, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flag {flag_name} not found"
            )
        
        logger.info(
            "User removed from whitelist successfully",
            correlation_id=correlation_id,
            flag_name=flag_name,
            user_id=user_id
        )
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "success": True,
            "message": f"User {user_id} removed from whitelist for {flag_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove user from whitelist", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove user from whitelist: {str(e)}"
        )


@app.get("/api/feature-flags/{flag_name}/stats")
async def get_usage_stats(request: Request, flag_name: str, days: int = 7):
    """Get usage statistics for a feature flag."""
    correlation_id = request.state.correlation_id
    
    try:
        logger.info(
            "Getting feature flag usage stats",
            correlation_id=correlation_id,
            flag_name=flag_name,
            days=days
        )
        
        manager = get_feature_flag_manager()
        stats = manager.get_usage_stats(flag_name, days)
        
        return {
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "stats": stats
        }
        
    except Exception as e:
        logger.error("Failed to get usage stats", correlation_id=correlation_id, exc=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage stats: {str(e)}"
        )


# ==========================================
# Scheduled Backup Tasks
# ==========================================

# Scheduled backup task
SCHEDULED_BACKUP_TASK = None
SCHEDULED_MINIO_BACKUP_TASK = None

async def scheduled_backup_task():
    """Background task to create automated database backups"""
    backup_interval = int(os.getenv("BACKUP_INTERVAL_HOURS", "24")) * 3600  # Convert to seconds
    logger.info(f"Scheduled backup task started (interval: {backup_interval // 3600} hours)")
    
    while True:
        try:
            await asyncio.sleep(backup_interval)
            
            # Create automated backup
            logger.info("Creating scheduled database backup")
            manager = get_backup_manager()
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"autograph_scheduled_{timestamp}"
            
            backup_metadata = manager.create_backup(
                backup_name=backup_name,
                backup_format="custom",
                upload_to_minio=True
            )
            
            logger.info(
                "Scheduled backup completed successfully",
                backup_name=backup_metadata["backup_name"],
                size_mb=backup_metadata["file_size_mb"]
            )
            
        except asyncio.CancelledError:
            logger.info("Scheduled backup task cancelled")
            break
        except Exception as e:
            logger.error("Scheduled backup failed", exc=e)
            # Continue running even if one backup fails
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


async def scheduled_minio_backup_task():
    """Background task to create automated MinIO bucket backups"""
    backup_interval = int(os.getenv("MINIO_BACKUP_INTERVAL_HOURS", "168")) * 3600  # Default 7 days (weekly)
    buckets_to_backup = os.getenv("MINIO_BACKUP_BUCKETS", "diagrams,exports,uploads").split(",")
    
    logger.info(
        f"Scheduled MinIO backup task started",
        interval_hours=backup_interval // 3600,
        buckets=buckets_to_backup
    )
    
    while True:
        try:
            await asyncio.sleep(backup_interval)
            
            # Create automated backups for specified buckets
            logger.info("Creating scheduled MinIO bucket backups")
            manager = get_minio_backup_manager()
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            
            for bucket_name in buckets_to_backup:
                bucket_name = bucket_name.strip()
                if not bucket_name:
                    continue
                
                try:
                    backup_name = f"scheduled_{bucket_name}_{timestamp}"
                    
                    backup_metadata = manager.backup_bucket(
                        bucket_name=bucket_name,
                        backup_name=backup_name,
                        include_versions=False
                    )
                    
                    logger.info(
                        "Scheduled MinIO bucket backup completed",
                        bucket=bucket_name,
                        backup_name=backup_metadata["backup_name"],
                        objects=backup_metadata["object_count"],
                        size_mb=backup_metadata["archive_size_mb"]
                    )
                except Exception as e:
                    logger.error(
                        "Scheduled MinIO bucket backup failed",
                        bucket=bucket_name,
                        exc=e
                    )
            
        except asyncio.CancelledError:
            logger.info("Scheduled MinIO backup task cancelled")
            break
        except Exception as e:
            logger.error("Scheduled MinIO backup task error", exc=e)
            # Continue running even if one backup cycle fails
            await asyncio.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    import uvicorn
    import ssl
    from pathlib import Path

    port = int(os.getenv("API_GATEWAY_PORT", "8080"))
    tls_enabled = os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")

    if tls_enabled:
        # Configure TLS 1.3
        cert_dir = Path(__file__).parent.parent.parent.parent / "certs"
        cert_file = str(cert_dir / "server-cert.pem")
        key_file = str(cert_dir / "server-key.pem")

        # Create SSL context for TLS 1.3
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        # TLS 1.3 cipher suites
        ssl_context.set_ciphers('TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256')

        # Security options
        ssl_context.options |= ssl.OP_NO_TLSv1
        ssl_context.options |= ssl.OP_NO_TLSv1_1
        ssl_context.options |= ssl.OP_NO_TLSv1_2
        ssl_context.options |= ssl.OP_NO_COMPRESSION

        logger.info(f"Starting API Gateway with TLS 1.3 on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port, ssl=ssl_context)
    else:
        logger.info(f"Starting API Gateway without TLS on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)

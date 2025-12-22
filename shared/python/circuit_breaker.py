"""Circuit breaker pattern implementation for preventing cascading failures.

The circuit breaker pattern protects services from being overwhelmed by failed
requests. It monitors for failures and "opens" the circuit when a threshold is
reached, allowing the failing service to recover without being bombarded with
additional requests.

Circuit Breaker States:
- CLOSED: Normal operation, requests pass through
- OPEN: Failure threshold reached, requests fail fast
- HALF_OPEN: Testing if service has recovered
"""
import time
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import logging
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation.
    
    Args:
        name: Name of the circuit breaker (for logging)
        failure_threshold: Number of failures before opening circuit
        timeout: Seconds to wait before trying again (moving to half-open)
        success_threshold: Number of successes needed to close circuit from half-open
        expected_exception: Exception type that triggers the circuit breaker
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        success_threshold: int = 2,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count
    
    @property
    def success_count(self) -> int:
        """Get current success count (in half-open state)."""
        return self._success_count
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Return value of func
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception raised by func
        """
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Service is unavailable. "
                        f"Last failure: {self._last_failure_time}"
                    )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try resetting the circuit."""
        if self._last_failure_time is None:
            return True
        return (datetime.now() - self._last_failure_time).total_seconds() >= self.timeout
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.info(
                    f"Circuit breaker '{self.name}' success in HALF_OPEN state "
                    f"({self._success_count}/{self.success_threshold})"
                )
                
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed in half-open state, go back to open
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' failed in HALF_OPEN state, "
                    f"moving back to OPEN"
                )
            elif self._failure_count >= self.failure_threshold:
                # Exceeded failure threshold, open the circuit
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' moved to OPEN state "
                    f"after {self._failure_count} failures"
                )
    
    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics.
        
        Returns:
            Dictionary with current state and counters
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout": self.timeout,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }


# Example usage:
# from shared.python.circuit_breaker import CircuitBreaker, CircuitBreakerError
# 
# # Create circuit breaker for external API
# api_breaker = CircuitBreaker(
#     name="external-api",
#     failure_threshold=5,  # Open after 5 failures
#     timeout=60,           # Wait 60s before trying again
#     success_threshold=2   # Need 2 successes to close
# )
# 
# # Use circuit breaker
# try:
#     result = api_breaker.call(make_api_request, url, data)
# except CircuitBreakerError:
#     # Circuit is open, fail fast
#     return {"error": "Service temporarily unavailable"}
# except Exception as e:
#     # Other error from the API
#     return {"error": str(e)}

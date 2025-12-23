"""Retry logic with exponential backoff for transient failures."""
import time
import asyncio
import logging
from functools import wraps
from typing import Callable, TypeVar, Optional, Type, Tuple
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds (default 1s)
            max_delay: Maximum delay in seconds (default 60s)
            exponential_base: Base for exponential backoff (default 2)
            jitter: Add random jitter to delays (default True)
            exceptions: Tuple of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.
        
        Uses exponential backoff: delay = initial_delay * (exponential_base ^ attempt)
        With optional jitter to prevent thundering herd.
        
        Args:
            attempt: Current attempt number (0-indexed)
        
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Add jitter (±25% randomization)
        if self.jitter:
            jitter_amount = delay * 0.25
            delay = delay + random.uniform(-jitter_amount, jitter_amount)
            delay = max(0.1, delay)  # Minimum 100ms delay
        
        return delay


def retry(config: Optional[RetryConfig] = None):
    """
    Decorator for synchronous functions with retry logic and exponential backoff.
    
    Example:
        @retry(RetryConfig(max_attempts=3, initial_delay=1.0))
        def fetch_data():
            # Function that might fail transiently
            return api_call()
    
    Args:
        config: RetryConfig instance (uses defaults if None)
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log success on retry
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except config.exceptions as e:
                    last_exception = e
                    
                    # Don't sleep after last attempt
                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(config: Optional[RetryConfig] = None):
    """
    Decorator for async functions with retry logic and exponential backoff.
    
    Example:
        @async_retry(RetryConfig(max_attempts=3, initial_delay=1.0))
        async def fetch_data():
            # Async function that might fail transiently
            return await api_call()
    
    Args:
        config: RetryConfig instance (uses defaults if None)
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log success on retry
                    if attempt > 0:
                        logger.info(
                            f"Retry succeeded for {func.__name__} on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except config.exceptions as e:
                    last_exception = e
                    
                    # Don't sleep after last attempt
                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator


# Common retry configurations
DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
    exceptions=(ConnectionError, TimeoutError, OSError)
)

API_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
    exceptions=(ConnectionError, TimeoutError)
)

REDIS_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_delay=0.5,
    max_delay=5.0,
    exponential_base=2.0,
    jitter=True,
    exceptions=(ConnectionError, TimeoutError)
)

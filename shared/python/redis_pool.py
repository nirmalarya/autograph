"""Redis connection pool configuration for high concurrency.

This module provides a centralized Redis connection pool that can be used
across all services for efficient connection management.
"""
import os
import redis
from redis.connection import ConnectionPool
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class RedisConnectionPool:
    """Redis connection pool manager."""
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    @classmethod
    def get_pool(cls, db: int = 0) -> ConnectionPool:
        """Get or create Redis connection pool.
        
        Args:
            db: Redis database number (0-15)
            
        Returns:
            ConnectionPool instance
        """
        if cls._pool is None:
            cls._pool = ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                db=db,
                max_connections=50,          # Maximum connections in pool
                socket_timeout=5,            # Socket timeout in seconds
                socket_connect_timeout=5,    # Connection timeout in seconds
                socket_keepalive=True,       # Enable TCP keepalive
                health_check_interval=30,    # Check connection health every 30s
                decode_responses=True,       # Decode responses to strings
                retry_on_timeout=True,       # Retry on timeout
            )
        return cls._pool
    
    @classmethod
    def get_client(cls, db: int = 0) -> redis.Redis:
        """Get Redis client with connection pooling.
        
        Args:
            db: Redis database number (0-15)
            
        Returns:
            Redis client instance
        """
        pool = cls.get_pool(db)
        return redis.Redis(connection_pool=pool)
    
    @classmethod
    def get_stats(cls) -> dict:
        """Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        if cls._pool is None:
            return {
                "initialized": False,
                "max_connections": 0,
                "connections_created": 0,
                "connections_available": 0,
                "connections_in_use": 0
            }
        
        # Get pool attributes that are available
        stats = {
            "initialized": True,
            "max_connections": cls._pool.max_connections if hasattr(cls._pool, 'max_connections') else 50,
        }
        
        # Try to get connection counts (may not be available in all Redis versions)
        try:
            if hasattr(cls._pool, '_created_connections'):
                created = cls._pool._created_connections
                stats["connections_created"] = created if isinstance(created, int) else len(created) if created else 0
            else:
                stats["connections_created"] = 0
                
            if hasattr(cls._pool, '_available_connections'):
                available = cls._pool._available_connections
                stats["connections_available"] = len(available) if hasattr(available, '__len__') else 0
            else:
                stats["connections_available"] = 0
                
            if hasattr(cls._pool, '_in_use_connections'):
                in_use = cls._pool._in_use_connections
                stats["connections_in_use"] = len(in_use) if hasattr(in_use, '__len__') else 0
            else:
                stats["connections_in_use"] = 0
        except Exception:
            # If we can't get detailed stats, just return basic info
            stats["connections_created"] = "N/A"
            stats["connections_available"] = "N/A"
            stats["connections_in_use"] = "N/A"
        
        return stats
    
    @classmethod
    def close(cls):
        """Close all connections in the pool."""
        if cls._pool is not None:
            cls._pool.disconnect()
            cls._pool = None
        if cls._client is not None:
            cls._client.close()
            cls._client = None


def get_redis_client(db: int = 0) -> redis.Redis:
    """Get Redis client with connection pooling.
    
    This is a convenience function for getting a Redis client.
    
    Args:
        db: Redis database number (0-15)
        
    Returns:
        Redis client instance
    """
    return RedisConnectionPool.get_client(db)


def get_redis_stats() -> dict:
    """Get Redis connection pool statistics.
    
    Returns:
        Dictionary with pool statistics
    """
    return RedisConnectionPool.get_stats()


# Example usage:
# from shared.python.redis_pool import get_redis_client
# 
# # Get Redis client for db 0 (default)
# redis_client = get_redis_client()
# redis_client.set("key", "value")
# 
# # Get Redis client for db 1 (e.g., for rate limiting)
# rate_limit_redis = get_redis_client(db=1)
# rate_limit_redis.incr("user:123:requests")
# 
# # Get pool statistics
# from shared.python.redis_pool import get_redis_stats
# stats = get_redis_stats()
# print(f"Pool has {stats['connections_in_use']} connections in use")

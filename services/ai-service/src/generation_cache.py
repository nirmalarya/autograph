"""
Generation Cache for AI Service

Features implemented:
- Feature #367: Generation cache - reuse recent generations
- Feature #368: Cache expiry mechanism
"""

import logging
import time
import hashlib
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CachedGeneration:
    """A cached diagram generation."""
    prompt_hash: str
    prompt: str
    mermaid_code: str
    diagram_type: str
    explanation: str
    provider: str
    model: str
    tokens_used: int
    timestamp: float
    quality_score: Optional[float] = None
    layout_algorithm: Optional[str] = None
    cache_hits: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "age_seconds": time.time() - self.timestamp,
            "created_at": datetime.fromtimestamp(self.timestamp).isoformat()
        }


class GenerationCache:
    """
    Cache for AI diagram generations.
    
    Features:
    - Feature #367: Reuse recent generations for identical prompts
    - Feature #368: Automatic cache expiry based on TTL
    """
    
    def __init__(
        self,
        max_size: int = 100,
        ttl_seconds: int = 3600  # 1 hour default
    ):
        """
        Initialize generation cache.
        
        Args:
            max_size: Maximum number of cached generations
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, CachedGeneration] = {}
        self.access_times: Dict[str, float] = {}
        
        logger.info(
            f"Initialized generation cache: max_size={max_size}, "
            f"ttl={ttl_seconds}s ({ttl_seconds/3600:.1f}h)"
        )
    
    def _hash_prompt(
        self,
        prompt: str,
        diagram_type: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        """
        Create hash of prompt and parameters.
        
        Args:
            prompt: User's diagram prompt
            diagram_type: Diagram type
            provider: AI provider
            model: AI model
            
        Returns:
            SHA256 hash string
        """
        # Include relevant parameters in hash
        key = json.dumps({
            "prompt": prompt.strip().lower(),
            "diagram_type": diagram_type,
            "provider": provider,
            "model": model
        }, sort_keys=True)
        
        return hashlib.sha256(key.encode()).hexdigest()
    
    def get(
        self,
        prompt: str,
        diagram_type: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[CachedGeneration]:
        """
        Feature #367: Get cached generation if available.
        
        Args:
            prompt: User's diagram prompt
            diagram_type: Diagram type
            provider: AI provider
            model: AI model
            
        Returns:
            CachedGeneration if found and not expired, None otherwise
        """
        prompt_hash = self._hash_prompt(prompt, diagram_type, provider, model)
        
        if prompt_hash not in self.cache:
            logger.debug(f"Cache MISS for prompt hash: {prompt_hash[:8]}...")
            return None
        
        cached = self.cache[prompt_hash]
        age = time.time() - cached.timestamp
        
        # Feature #368: Check if entry has expired
        if age > self.ttl_seconds:
            logger.info(
                f"Cache entry expired (age={age:.1f}s, ttl={self.ttl_seconds}s), "
                f"removing: {prompt_hash[:8]}..."
            )
            del self.cache[prompt_hash]
            del self.access_times[prompt_hash]
            return None
        
        # Update access time and hit count
        self.access_times[prompt_hash] = time.time()
        cached.cache_hits += 1
        
        logger.info(
            f"Cache HIT (hits={cached.cache_hits}, age={age:.1f}s): "
            f"{prompt_hash[:8]}... -> {cached.diagram_type}"
        )
        
        return cached
    
    def put(
        self,
        prompt: str,
        mermaid_code: str,
        diagram_type: str,
        explanation: str,
        provider: str,
        model: str,
        tokens_used: int,
        quality_score: Optional[float] = None,
        layout_algorithm: Optional[str] = None
    ) -> str:
        """
        Feature #367: Store generation in cache.
        
        Args:
            prompt: User's diagram prompt
            mermaid_code: Generated Mermaid code
            diagram_type: Type of diagram
            explanation: AI explanation
            provider: AI provider used
            model: AI model used
            tokens_used: Token count
            quality_score: Quality score if available
            layout_algorithm: Layout algorithm used
            
        Returns:
            Prompt hash (cache key)
        """
        prompt_hash = self._hash_prompt(prompt, diagram_type, provider, model)
        
        # Create cache entry
        cached = CachedGeneration(
            prompt_hash=prompt_hash,
            prompt=prompt,
            mermaid_code=mermaid_code,
            diagram_type=diagram_type,
            explanation=explanation,
            provider=provider,
            model=model,
            tokens_used=tokens_used,
            timestamp=time.time(),
            quality_score=quality_score,
            layout_algorithm=layout_algorithm,
            cache_hits=0
        )
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[prompt_hash] = cached
        self.access_times[prompt_hash] = time.time()
        
        logger.info(
            f"Cached generation: {prompt_hash[:8]}... -> {diagram_type} "
            f"(cache size: {len(self.cache)}/{self.max_size})"
        )
        
        return prompt_hash
    
    def _evict_oldest(self):
        """Evict least recently accessed entry."""
        if not self.access_times:
            return
        
        # Find oldest access time
        oldest_key = min(self.access_times, key=self.access_times.get)
        
        logger.debug(f"Evicting oldest cache entry: {oldest_key[:8]}...")
        
        del self.cache[oldest_key]
        del self.access_times[oldest_key]
    
    def invalidate(self, prompt_hash: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            prompt_hash: Hash of the prompt to invalidate
            
        Returns:
            True if entry was removed, False if not found
        """
        if prompt_hash in self.cache:
            del self.cache[prompt_hash]
            del self.access_times[prompt_hash]
            logger.info(f"Invalidated cache entry: {prompt_hash[:8]}...")
            return True
        return False
    
    def clear(self):
        """Clear entire cache."""
        count = len(self.cache)
        self.cache.clear()
        self.access_times.clear()
        logger.info(f"Cleared cache ({count} entries removed)")
    
    def cleanup_expired(self) -> int:
        """
        Feature #368: Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for key, cached in self.cache.items():
            age = current_time - cached.timestamp
            if age > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            del self.access_times[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.cache:
            return {
                "size": 0,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hit_rate": 0.0,
                "total_hits": 0,
                "entries": []
            }
        
        total_hits = sum(c.cache_hits for c in self.cache.values())
        total_requests = total_hits + len(self.cache)  # hits + initial puts
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "hit_rate": total_hits / total_requests if total_requests > 0 else 0.0,
            "total_hits": total_hits,
            "entries": [
                {
                    "prompt_hash": key[:16],
                    "diagram_type": cached.diagram_type,
                    "provider": cached.provider,
                    "age_seconds": time.time() - cached.timestamp,
                    "cache_hits": cached.cache_hits,
                    "prompt_preview": cached.prompt[:50] + "..." if len(cached.prompt) > 50 else cached.prompt
                }
                for key, cached in sorted(
                    self.cache.items(),
                    key=lambda x: x[1].cache_hits,
                    reverse=True
                )[:10]  # Top 10 most hit entries
            ]
        }
    
    def get_all_cached(self) -> List[Dict[str, Any]]:
        """
        Get all cached generations.
        
        Returns:
            List of cached generation dictionaries
        """
        return [cached.to_dict() for cached in self.cache.values()]


# Global cache instance
_generation_cache = GenerationCache()


def get_generation_cache() -> GenerationCache:
    """Get global generation cache instance."""
    return _generation_cache

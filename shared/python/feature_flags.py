"""
Feature Flag System for AutoGraph v3

This module provides a flexible feature flag system for gradual feature rollout.
Features can be enabled for:
- Percentage of users (10%, 50%, 100%)
- Specific user IDs (for testing)
- Specific environments (dev, staging, prod)

Flags are stored in Redis for fast lookups and support hot-reloading.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import redis

logger = logging.getLogger(__name__)


class RolloutStrategy(str, Enum):
    """Rollout strategy for feature flags."""
    PERCENTAGE = "percentage"  # Gradually roll out to percentage of users
    WHITELIST = "whitelist"  # Enable for specific user IDs
    BLACKLIST = "blacklist"  # Disable for specific user IDs
    ENVIRONMENT = "environment"  # Enable based on environment


class FeatureFlag:
    """Represents a feature flag configuration."""

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        description: str = "",
        rollout_percentage: int = 0,
        strategy: RolloutStrategy = RolloutStrategy.PERCENTAGE,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
        environments: Optional[List[str]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.enabled = enabled
        self.description = description
        self.rollout_percentage = max(0, min(100, rollout_percentage))
        self.strategy = strategy
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
        self.environments = set(environments or [])
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "description": self.description,
            "rollout_percentage": self.rollout_percentage,
            "strategy": self.strategy.value,
            "whitelist": list(self.whitelist),
            "blacklist": list(self.blacklist),
            "environments": list(self.environments),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureFlag":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            enabled=data.get("enabled", False),
            description=data.get("description", ""),
            rollout_percentage=data.get("rollout_percentage", 0),
            strategy=RolloutStrategy(data.get("strategy", RolloutStrategy.PERCENTAGE.value)),
            whitelist=data.get("whitelist", []),
            blacklist=data.get("blacklist", []),
            environments=data.get("environments", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else None,
            metadata=data.get("metadata", {}),
        )


class FeatureFlagManager:
    """Manages feature flags with Redis backend."""

    def __init__(self, redis_client: redis.Redis, key_prefix: str = "feature_flag:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.cache_ttl = 300  # 5 minutes cache

    def _get_flag_key(self, flag_name: str) -> str:
        """Get Redis key for flag."""
        return f"{self.key_prefix}{flag_name}"

    def _get_all_flags_key(self) -> str:
        """Get Redis key for all flags list."""
        return f"{self.key_prefix}all"

    def _get_usage_key(self, flag_name: str) -> str:
        """Get Redis key for usage tracking."""
        return f"{self.key_prefix}usage:{flag_name}"

    def create_flag(self, flag: FeatureFlag) -> bool:
        """Create a new feature flag."""
        try:
            key = self._get_flag_key(flag.name)
            
            # Check if flag already exists
            if self.redis.exists(key):
                logger.warning(f"Flag {flag.name} already exists")
                return False

            # Store flag data
            self.redis.set(key, json.dumps(flag.to_dict()))
            
            # Add to all flags set
            self.redis.sadd(self._get_all_flags_key(), flag.name)
            
            logger.info(f"Created feature flag: {flag.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create flag {flag.name}: {e}")
            return False

    def update_flag(self, flag: FeatureFlag) -> bool:
        """Update an existing feature flag."""
        try:
            key = self._get_flag_key(flag.name)
            
            # Check if flag exists
            if not self.redis.exists(key):
                logger.warning(f"Flag {flag.name} does not exist")
                return False

            # Update timestamp
            flag.updated_at = datetime.utcnow()
            
            # Store updated flag data
            self.redis.set(key, json.dumps(flag.to_dict()))
            
            logger.info(f"Updated feature flag: {flag.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update flag {flag.name}: {e}")
            return False

    def get_flag(self, flag_name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        try:
            key = self._get_flag_key(flag_name)
            data = self.redis.get(key)
            
            if not data:
                return None
                
            return FeatureFlag.from_dict(json.loads(data))

        except Exception as e:
            logger.error(f"Failed to get flag {flag_name}: {e}")
            return None

    def delete_flag(self, flag_name: str) -> bool:
        """Delete a feature flag."""
        try:
            key = self._get_flag_key(flag_name)
            usage_key = self._get_usage_key(flag_name)
            
            # Delete flag data
            self.redis.delete(key)
            
            # Delete usage data
            self.redis.delete(usage_key)
            
            # Remove from all flags set
            self.redis.srem(self._get_all_flags_key(), flag_name)
            
            logger.info(f"Deleted feature flag: {flag_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete flag {flag_name}: {e}")
            return False

    def list_flags(self) -> List[FeatureFlag]:
        """List all feature flags."""
        try:
            all_flags_key = self._get_all_flags_key()
            flag_names = self.redis.smembers(all_flags_key)
            
            flags = []
            for name_bytes in flag_names:
                name = name_bytes.decode() if isinstance(name_bytes, bytes) else name_bytes
                flag = self.get_flag(name)
                if flag:
                    flags.append(flag)
            
            return sorted(flags, key=lambda f: f.name)

        except Exception as e:
            logger.error(f"Failed to list flags: {e}")
            return []

    def is_enabled(
        self,
        flag_name: str,
        user_id: Optional[str] = None,
        environment: Optional[str] = None,
        default: bool = False,
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.
        
        Args:
            flag_name: Name of the feature flag
            user_id: User ID to check (optional)
            environment: Environment to check (optional)
            default: Default value if flag not found
            
        Returns:
            True if feature is enabled, False otherwise
        """
        try:
            flag = self.get_flag(flag_name)
            
            if not flag:
                logger.debug(f"Flag {flag_name} not found, using default: {default}")
                return default

            # If flag is globally disabled, return False
            if not flag.enabled:
                return False

            # Check blacklist first
            if user_id and user_id in flag.blacklist:
                logger.debug(f"User {user_id} is blacklisted for flag {flag_name}")
                return False

            # Check whitelist
            if user_id and user_id in flag.whitelist:
                logger.debug(f"User {user_id} is whitelisted for flag {flag_name}")
                self._track_usage(flag_name, user_id, True)
                return True

            # Check environment
            if environment and flag.environments:
                enabled = environment in flag.environments
                logger.debug(f"Flag {flag_name} environment check for {environment}: {enabled}")
                if not enabled:
                    return False

            # Check percentage rollout
            if flag.strategy == RolloutStrategy.PERCENTAGE and user_id:
                enabled = self._is_in_rollout_percentage(flag_name, user_id, flag.rollout_percentage)
                logger.debug(f"Flag {flag_name} percentage check for user {user_id}: {enabled}")
                self._track_usage(flag_name, user_id, enabled)
                return enabled

            # If no user_id provided for percentage rollout, use flag.enabled
            if flag.strategy == RolloutStrategy.PERCENTAGE and not user_id:
                return flag.rollout_percentage >= 100

            # Default to flag.enabled
            return flag.enabled

        except Exception as e:
            logger.error(f"Error checking flag {flag_name}: {e}")
            return default

    def _is_in_rollout_percentage(self, flag_name: str, user_id: str, percentage: int) -> bool:
        """
        Determine if user is in rollout percentage using consistent hashing.
        
        This ensures the same user always gets the same result for a flag,
        providing a stable experience.
        """
        if percentage <= 0:
            return False
        if percentage >= 100:
            return True

        # Create a hash of flag_name + user_id for consistent distribution
        hash_input = f"{flag_name}:{user_id}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Convert first 8 characters of hash to integer
        hash_int = int(hash_value[:8], 16)
        
        # Calculate percentage bucket (0-99)
        bucket = hash_int % 100
        
        # User is in rollout if their bucket is less than percentage
        return bucket < percentage

    def _track_usage(self, flag_name: str, user_id: str, enabled: bool):
        """Track feature flag usage for analytics."""
        try:
            usage_key = self._get_usage_key(flag_name)
            timestamp = datetime.utcnow().isoformat()
            
            usage_data = {
                "user_id": user_id,
                "enabled": enabled,
                "timestamp": timestamp,
            }
            
            # Store in sorted set with timestamp as score
            score = datetime.utcnow().timestamp()
            self.redis.zadd(usage_key, {json.dumps(usage_data): score})
            
            # Keep only last 7 days of usage data
            cutoff = (datetime.utcnow() - timedelta(days=7)).timestamp()
            self.redis.zremrangebyscore(usage_key, 0, cutoff)

        except Exception as e:
            logger.error(f"Failed to track usage for {flag_name}: {e}")

    def get_usage_stats(self, flag_name: str, days: int = 7) -> Dict[str, Any]:
        """Get usage statistics for a feature flag."""
        try:
            usage_key = self._get_usage_key(flag_name)
            
            # Get usage data for specified days
            cutoff = (datetime.utcnow() - timedelta(days=days)).timestamp()
            usage_data = self.redis.zrangebyscore(usage_key, cutoff, "+inf")
            
            total_checks = len(usage_data)
            enabled_count = 0
            unique_users = set()
            
            for data_bytes in usage_data:
                data = json.loads(data_bytes.decode() if isinstance(data_bytes, bytes) else data_bytes)
                if data.get("enabled"):
                    enabled_count += 1
                unique_users.add(data.get("user_id"))
            
            return {
                "flag_name": flag_name,
                "total_checks": total_checks,
                "enabled_count": enabled_count,
                "disabled_count": total_checks - enabled_count,
                "unique_users": len(unique_users),
                "enabled_percentage": (enabled_count / total_checks * 100) if total_checks > 0 else 0,
                "days": days,
            }

        except Exception as e:
            logger.error(f"Failed to get usage stats for {flag_name}: {e}")
            return {
                "flag_name": flag_name,
                "error": str(e),
            }

    def set_rollout_percentage(self, flag_name: str, percentage: int) -> bool:
        """Set the rollout percentage for a flag."""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                logger.warning(f"Flag {flag_name} not found")
                return False

            flag.rollout_percentage = max(0, min(100, percentage))
            flag.strategy = RolloutStrategy.PERCENTAGE
            
            return self.update_flag(flag)

        except Exception as e:
            logger.error(f"Failed to set rollout percentage for {flag_name}: {e}")
            return False

    def add_to_whitelist(self, flag_name: str, user_id: str) -> bool:
        """Add a user to the whitelist for a flag."""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                logger.warning(f"Flag {flag_name} not found")
                return False

            flag.whitelist.add(user_id)
            return self.update_flag(flag)

        except Exception as e:
            logger.error(f"Failed to add {user_id} to whitelist for {flag_name}: {e}")
            return False

    def remove_from_whitelist(self, flag_name: str, user_id: str) -> bool:
        """Remove a user from the whitelist for a flag."""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                logger.warning(f"Flag {flag_name} not found")
                return False

            flag.whitelist.discard(user_id)
            return self.update_flag(flag)

        except Exception as e:
            logger.error(f"Failed to remove {user_id} from whitelist for {flag_name}: {e}")
            return False

    def add_to_blacklist(self, flag_name: str, user_id: str) -> bool:
        """Add a user to the blacklist for a flag."""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                logger.warning(f"Flag {flag_name} not found")
                return False

            flag.blacklist.add(user_id)
            return self.update_flag(flag)

        except Exception as e:
            logger.error(f"Failed to add {user_id} to blacklist for {flag_name}: {e}")
            return False

    def remove_from_blacklist(self, flag_name: str, user_id: str) -> bool:
        """Remove a user from the blacklist for a flag."""
        try:
            flag = self.get_flag(flag_name)
            if not flag:
                logger.warning(f"Flag {flag_name} not found")
                return False

            flag.blacklist.discard(user_id)
            return self.update_flag(flag)

        except Exception as e:
            logger.error(f"Failed to remove {user_id} from blacklist for {flag_name}: {e}")
            return False

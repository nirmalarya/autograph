"""
Shared configuration module for AutoGraph v3 services.
Supports environment-based configuration (local, docker, kubernetes).
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration manager for AutoGraph v3.
    Loads environment-specific configuration and validates required settings.
    """
    
    def __init__(self, env: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env: Environment name (local, docker, kubernetes). 
                 If None, reads from ENV environment variable or defaults to 'local'.
        """
        # Determine environment
        self.env = env or os.getenv("ENV", "local")
        
        # Load environment-specific configuration
        self._load_env_file()
        
        # Validate required configuration
        self._validate_required()
    
    def _load_env_file(self):
        """Load environment-specific .env file."""
        # Find project root (look for .git directory)
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir
        while project_root.parent != project_root:
            if (project_root / ".git").exists():
                break
            project_root = project_root.parent
        
        # Load environment-specific .env file FIRST (highest priority after OS env vars)
        env_file = project_root / f".env.{self.env}"
        if env_file.exists():
            load_dotenv(env_file, override=False)  # Don't override OS environment variables
            logger.info(f"Loaded {self.env} configuration from {env_file}")
        else:
            logger.warning(f"Environment file not found: {env_file}")
        
        # Load base .env as fallback for missing values
        base_env = project_root / ".env"
        if base_env.exists():
            load_dotenv(base_env, override=False)  # Only load values not already set
            logger.info(f"Loaded base configuration from {base_env} (fallback)")

    
    def _validate_required(self):
        """Validate required configuration variables."""
        required = [
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "REDIS_HOST",
            "REDIS_PORT",
            "JWT_SECRET",
        ]
        
        missing = [key for key in required if not os.getenv(key)]
        
        if missing:
            raise ValueError(
                f"Missing required configuration variables: {', '.join(missing)}\n"
                f"Current environment: {self.env}\n"
                f"Please set these in .env.{self.env} or as environment variables."
            )
        
        logger.info(f"Configuration validated for environment: {self.env}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return os.getenv(key, default)
    
    def get_int(self, key: str, default: int) -> int:
        """
        Get integer configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Integer configuration value or default
        """
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer for {key}: {value}, using default: {default}")
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """
        Get boolean configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Boolean configuration value or default
        """
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.env == "local"
    
    @property
    def is_docker(self) -> bool:
        """Check if running in Docker environment."""
        return self.env == "docker"
    
    @property
    def is_kubernetes(self) -> bool:
        """Check if running in Kubernetes environment."""
        return self.env == "kubernetes"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env in ("docker", "kubernetes")
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL."""
        return (
            f"postgresql://{self.get('POSTGRES_USER')}:"
            f"{self.get('POSTGRES_PASSWORD')}@"
            f"{self.get('POSTGRES_HOST')}:{self.get('POSTGRES_PORT')}/"
            f"{self.get('POSTGRES_DB')}"
        )
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        password = self.get('REDIS_PASSWORD')
        if password:
            return f"redis://:{password}@{self.get('REDIS_HOST')}:{self.get('REDIS_PORT')}"
        return f"redis://{self.get('REDIS_HOST')}:{self.get('REDIS_PORT')}"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Config(env={self.env})"


# Global configuration instance
_config: Optional[Config] = None


def get_config(env: Optional[str] = None) -> Config:
    """
    Get global configuration instance.
    
    Args:
        env: Environment name (local, docker, kubernetes).
             If None, uses existing instance or creates new with default env.
    
    Returns:
        Configuration instance
    """
    global _config
    
    if _config is None or (env is not None and env != _config.env):
        _config = Config(env)
    
    return _config


def reload_config(env: Optional[str] = None):
    """
    Reload configuration (useful for testing).
    
    Args:
        env: Environment name to load
    """
    global _config
    _config = Config(env)

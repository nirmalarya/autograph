"""
Secrets Management Module for AutoGraph v3.

Provides encrypted storage and retrieval of sensitive configuration values
like database passwords, API keys, and JWT secrets.

Features:
- Encryption at rest using Fernet (symmetric encryption)
- Audit logging of all secret access
- Key rotation support
- Environment-based key management
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Manages encrypted storage and retrieval of secrets.

    Secrets are encrypted using Fernet (symmetric encryption) with a key
    derived from a master password and salt. All secret access is logged
    for audit purposes.
    """

    def __init__(self,
                 master_key: Optional[str] = None,
                 secrets_file: Optional[str] = None,
                 audit_log_file: Optional[str] = None):
        """
        Initialize secrets manager.

        Args:
            master_key: Master encryption key (base64-encoded Fernet key).
                       If None, reads from SECRETS_MASTER_KEY env var.
            secrets_file: Path to encrypted secrets storage file.
                         If None, uses {project_root}/shared/secrets.enc
            audit_log_file: Path to audit log file.
                           If None, uses {project_root}/logs/secrets_audit.log
        """
        # Get master key from environment or parameter
        self.master_key = master_key or os.getenv("SECRETS_MASTER_KEY")
        if not self.master_key:
            # Generate a new master key if none exists (development only)
            logger.warning("No SECRETS_MASTER_KEY found, generating new key (DEV ONLY)")
            self.master_key = Fernet.generate_key().decode()

        # Initialize Fernet cipher
        try:
            self.cipher = Fernet(self.master_key.encode())
        except Exception as e:
            raise ValueError(f"Invalid master key: {e}")

        # Set up secrets file path
        if secrets_file:
            self.secrets_file = Path(secrets_file)
        else:
            project_root = self._find_project_root()
            secrets_dir = project_root / "shared"
            secrets_dir.mkdir(exist_ok=True)
            self.secrets_file = secrets_dir / "secrets.enc"

        # Set up audit log file path
        if audit_log_file:
            self.audit_log_file = Path(audit_log_file)
        else:
            project_root = self._find_project_root()
            logs_dir = project_root / "logs"
            logs_dir.mkdir(exist_ok=True)
            self.audit_log_file = logs_dir / "secrets_audit.log"

        # Load or initialize secrets storage
        self.secrets: Dict[str, str] = self._load_secrets()

    def _find_project_root(self) -> Path:
        """Find project root directory (contains .git)."""
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir
        while project_root.parent != project_root:
            if (project_root / ".git").exists():
                return project_root
            project_root = project_root.parent
        return current_dir

    def _load_secrets(self) -> Dict[str, str]:
        """Load encrypted secrets from storage file."""
        if not self.secrets_file.exists():
            logger.info(f"Secrets file not found, creating new: {self.secrets_file}")
            return {}

        try:
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher.decrypt(encrypted_data)
                secrets = json.loads(decrypted_data.decode())
                logger.info(f"Loaded {len(secrets)} secrets from {self.secrets_file}")
                return secrets
        except Exception as e:
            logger.error(f"Error loading secrets: {e}")
            return {}

    def _save_secrets(self):
        """Save encrypted secrets to storage file."""
        try:
            # Serialize secrets to JSON
            json_data = json.dumps(self.secrets, indent=2)

            # Encrypt the data
            encrypted_data = self.cipher.encrypt(json_data.encode())

            # Write to file
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)

            logger.info(f"Saved {len(self.secrets)} secrets to {self.secrets_file}")
            self._audit_log("SAVE_SECRETS", f"Saved {len(self.secrets)} secrets")
        except Exception as e:
            logger.error(f"Error saving secrets: {e}")
            raise

    def _audit_log(self, action: str, details: str, secret_name: Optional[str] = None):
        """
        Log secret access for audit purposes.

        Args:
            action: Action performed (GET, SET, DELETE, ROTATE, etc.)
            details: Additional details about the action
            secret_name: Name of the secret (if applicable)
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "secret_name": secret_name,
            "details": details,
            "pid": os.getpid()
        }

        try:
            with open(self.audit_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")

    def set_secret(self, name: str, value: str) -> bool:
        """
        Store a secret in encrypted storage.

        Args:
            name: Secret name/key
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        try:
            self.secrets[name] = value
            self._save_secrets()
            self._audit_log("SET_SECRET", f"Set secret: {name}", secret_name=name)
            logger.info(f"Secret '{name}' stored successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting secret '{name}': {e}")
            return False

    def get_secret(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret from encrypted storage.

        Args:
            name: Secret name/key
            default: Default value if secret not found

        Returns:
            Secret value or default if not found
        """
        value = self.secrets.get(name, default)

        if value is not None:
            self._audit_log("GET_SECRET", f"Retrieved secret: {name}", secret_name=name)
            logger.debug(f"Secret '{name}' retrieved successfully")
        else:
            logger.warning(f"Secret '{name}' not found")

        return value

    def delete_secret(self, name: str) -> bool:
        """
        Delete a secret from encrypted storage.

        Args:
            name: Secret name/key

        Returns:
            True if deleted, False if not found
        """
        if name in self.secrets:
            del self.secrets[name]
            self._save_secrets()
            self._audit_log("DELETE_SECRET", f"Deleted secret: {name}", secret_name=name)
            logger.info(f"Secret '{name}' deleted successfully")
            return True
        else:
            logger.warning(f"Secret '{name}' not found for deletion")
            return False

    def rotate_secret(self, name: str, new_value: str) -> bool:
        """
        Rotate a secret (update its value).

        Args:
            name: Secret name/key
            new_value: New secret value

        Returns:
            True if successful, False otherwise
        """
        old_exists = name in self.secrets
        self.secrets[name] = new_value
        self._save_secrets()

        action = "ROTATE_SECRET" if old_exists else "CREATE_SECRET"
        self._audit_log(action, f"Rotated secret: {name}", secret_name=name)
        logger.info(f"Secret '{name}' rotated successfully")
        return True

    def list_secrets(self) -> list:
        """
        List all secret names (not values).

        Returns:
            List of secret names
        """
        self._audit_log("LIST_SECRETS", f"Listed {len(self.secrets)} secret names")
        return list(self.secrets.keys())

    def verify_encryption(self, name: str) -> bool:
        """
        Verify that a secret is properly encrypted in storage.

        Args:
            name: Secret name to verify

        Returns:
            True if secret exists and is encrypted, False otherwise
        """
        if name not in self.secrets:
            logger.warning(f"Secret '{name}' not found for verification")
            return False

        try:
            # Read raw file to verify it's encrypted
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()

            # Verify the secret value is NOT in plaintext in the file
            secret_value = self.secrets[name]
            is_encrypted = secret_value.encode() not in encrypted_data

            self._audit_log("VERIFY_ENCRYPTION",
                          f"Verified encryption for secret: {name} (encrypted={is_encrypted})",
                          secret_name=name)

            return is_encrypted
        except Exception as e:
            logger.error(f"Error verifying encryption for '{name}': {e}")
            return False

    def get_audit_logs(self, limit: int = 100) -> list:
        """
        Retrieve audit logs.

        Args:
            limit: Maximum number of log entries to return

        Returns:
            List of audit log entries (most recent first)
        """
        try:
            with open(self.audit_log_file, 'r') as f:
                lines = f.readlines()

            # Parse JSON lines and return most recent first
            logs = [json.loads(line) for line in lines if line.strip()]
            return logs[-limit:][::-1]  # Most recent first
        except Exception as e:
            logger.error(f"Error reading audit logs: {e}")
            return []


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(master_key: Optional[str] = None) -> SecretsManager:
    """
    Get global secrets manager instance.

    Args:
        master_key: Master encryption key (optional, reads from env if not provided)

    Returns:
        SecretsManager instance
    """
    global _secrets_manager

    if _secrets_manager is None:
        _secrets_manager = SecretsManager(master_key=master_key)

    return _secrets_manager


def get_secret_or_env(secret_name: str, env_var: str, default: Optional[str] = None) -> Optional[str]:
    """
    Helper function to get value from secrets manager or fall back to environment variable.

    This allows gradual migration: try secrets manager first, fall back to env var.

    Args:
        secret_name: Name in secrets manager
        env_var: Environment variable name
        default: Default value if neither found

    Returns:
        Secret value, env var value, or default
    """
    try:
        sm = get_secrets_manager()
        value = sm.get_secret(secret_name)
        if value is not None:
            return value
    except Exception as e:
        logger.warning(f"Error accessing secrets manager: {e}")

    # Fall back to environment variable
    return os.getenv(env_var, default)

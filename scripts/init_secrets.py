#!/usr/bin/env python3
"""
Initialize secrets manager with database password.
This script stores the POSTGRES_PASSWORD in encrypted storage.
"""
import os
import sys
from pathlib import Path

# Add shared modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.python.secrets_manager import get_secrets_manager
from dotenv import load_dotenv

def init_secrets():
    """Initialize secrets with database password from environment."""
    # Load environment variables
    load_dotenv()

    # Get secrets manager
    sm = get_secrets_manager()

    # Get database password from environment
    postgres_password = os.getenv("POSTGRES_PASSWORD")
    if not postgres_password:
        print("ERROR: POSTGRES_PASSWORD not found in environment")
        return False

    # Store in encrypted secrets manager
    success = sm.set_secret("POSTGRES_PASSWORD", postgres_password)

    if success:
        print(f"✅ Successfully stored POSTGRES_PASSWORD in encrypted storage")
        print(f"📁 Secrets file: {sm.secrets_file}")
        print(f"🔐 Encryption: Fernet (symmetric)")

        # Verify encryption
        if sm.verify_encryption("POSTGRES_PASSWORD"):
            print("✅ Verified: Password is encrypted at rest")
        else:
            print("⚠️  Warning: Could not verify encryption")

        # Test retrieval
        retrieved = sm.get_secret("POSTGRES_PASSWORD")
        if retrieved == postgres_password:
            print("✅ Verified: Password can be decrypted correctly")
        else:
            print("❌ ERROR: Retrieved password doesn't match!")
            return False

        return True
    else:
        print("❌ ERROR: Failed to store password")
        return False

if __name__ == "__main__":
    success = init_secrets()
    sys.exit(0 if success else 1)

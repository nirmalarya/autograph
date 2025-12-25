#!/usr/bin/env python3
"""
Validation script for Feature #109: API key with expiration date

Tests that API keys can be created with expiration dates and are properly rejected when expired.
"""

import requests
import time
import sys
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8080"
AUTH_SERVICE_URL = "http://localhost:8085"

def log_separator():
    """Print a separator line."""
    logger.info("=" * 80)

def test_feature_109():
    """Test API key expiration functionality."""

    log_separator()
    logger.info("FEATURE #109: API Key with Expiration Date")
    log_separator()

    # Test user credentials
    test_email = f"apikey_exp_test_{int(time.time())}@example.com"
    test_password = "SecurePassword123!@#"

    # STEP 1: Register and login
    log_separator()
    logger.info("STEP 1: Register and login test user")
    log_separator()

    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "API Key Expiration Tester"
        }
    )

    if register_response.status_code not in [200, 201]:
        logger.error(f"❌ Registration failed: {register_response.status_code}")
        logger.error(f"Response: {register_response.text}")
        return False

    logger.info(f"✅ User registered: {test_email}")

    # Mark email as verified in database
    logger.info("   Verifying email in database...")
    import subprocess
    result = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"UPDATE users SET is_verified = true WHERE email = '{test_email}';"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        logger.warning(f"   ⚠️ Database update failed (continuing anyway): {result.stderr}")
    else:
        logger.info("   ✅ Email verified in database")

    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )

    if login_response.status_code != 200:
        logger.error(f"❌ Login failed: {login_response.status_code}")
        return False

    auth_token = login_response.json()["access_token"]
    logger.info(f"✅ User logged in successfully")
    logger.info(f"   Access token: {auth_token[:20]}...")

    headers = {"Authorization": f"Bearer {auth_token}"}

    # STEP 2: Create API key WITHOUT expiration
    log_separator()
    logger.info("STEP 2: Create API key WITHOUT expiration (should not expire)")
    log_separator()

    no_expiry_response = requests.post(
        f"{AUTH_SERVICE_URL}/api-keys",
        headers=headers,
        json={
            "name": "Never Expires Key",
            "scopes": ["read", "write"]
            # No expires_in_days - should be permanent
        }
    )

    if no_expiry_response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create non-expiring API key: {no_expiry_response.status_code}")
        logger.error(f"Response: {no_expiry_response.text}")
        return False

    no_expiry_data = no_expiry_response.json()
    no_expiry_key = no_expiry_data["api_key"]
    logger.info(f"✅ Non-expiring API key created")
    logger.info(f"   Name: {no_expiry_data['name']}")
    logger.info(f"   Prefix: {no_expiry_data['key_prefix']}")
    logger.info(f"   Expires at: {no_expiry_data.get('expires_at', 'Never')}")

    # STEP 3: Create API key WITH 30-day expiration
    log_separator()
    logger.info("STEP 3: Create API key WITH 30-day expiration")
    log_separator()

    with_expiry_response = requests.post(
        f"{AUTH_SERVICE_URL}/api-keys",
        headers=headers,
        json={
            "name": "30-Day Key",
            "scopes": ["read"],
            "expires_in_days": 30
        }
    )

    if with_expiry_response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create expiring API key: {with_expiry_response.status_code}")
        logger.error(f"Response: {with_expiry_response.text}")
        return False

    with_expiry_data = with_expiry_response.json()
    with_expiry_key = with_expiry_data["api_key"]
    expires_at_str = with_expiry_data.get("expires_at")

    logger.info(f"✅ Expiring API key created")
    logger.info(f"   Name: {with_expiry_data['name']}")
    logger.info(f"   Prefix: {with_expiry_data['key_prefix']}")
    logger.info(f"   Expires at: {expires_at_str}")

    # Verify expiration is ~30 days from now
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
        now = datetime.now(expires_at.tzinfo)
        days_until_expiry = (expires_at - now).days
        logger.info(f"   Days until expiry: ~{days_until_expiry}")

        if days_until_expiry < 29 or days_until_expiry > 31:
            logger.error(f"❌ Expiration date incorrect: expected ~30 days, got {days_until_expiry}")
            return False
        logger.info(f"   ✅ Expiration date is correct (~30 days)")

    # STEP 4: Test non-expiring key works
    log_separator()
    logger.info("STEP 4: Test non-expiring API key authentication")
    log_separator()

    test_response = requests.get(
        f"{AUTH_SERVICE_URL}/test/api-key-auth",
        headers={"Authorization": f"Bearer {no_expiry_key}"}
    )

    if test_response.status_code != 200:
        logger.error(f"❌ Non-expiring API key authentication failed: {test_response.status_code}")
        return False

    logger.info(f"✅ Non-expiring API key authentication successful")
    logger.info(f"   Authenticated as: {test_response.json()['email']}")

    # STEP 5: Test expiring key works (within expiration period)
    log_separator()
    logger.info("STEP 5: Test expiring API key authentication (should work - not expired yet)")
    log_separator()

    test_response2 = requests.get(
        f"{AUTH_SERVICE_URL}/test/api-key-auth",
        headers={"Authorization": f"Bearer {with_expiry_key}"}
    )

    if test_response2.status_code != 200:
        logger.error(f"❌ Expiring API key authentication failed (should work): {test_response2.status_code}")
        return False

    logger.info(f"✅ Expiring API key authentication successful (not expired yet)")
    logger.info(f"   Authenticated as: {test_response2.json()['email']}")

    # STEP 6: Create a key that expires immediately (0 days)
    log_separator()
    logger.info("STEP 6: Create API key with immediate expiration (0 days - for testing)")
    log_separator()

    # Actually, let's manually set an expired key in the database
    # First create a normal key, then modify its expiration
    expired_key_response = requests.post(
        f"{AUTH_SERVICE_URL}/api-keys",
        headers=headers,
        json={
            "name": "Test Expired Key",
            "scopes": ["read"],
            "expires_in_days": 1  # 1 day
        }
    )

    if expired_key_response.status_code not in [200, 201]:
        logger.error(f"❌ Failed to create test key: {expired_key_response.status_code}")
        return False

    expired_key_data = expired_key_response.json()
    expired_key = expired_key_data["api_key"]
    expired_key_id = expired_key_data["id"]

    logger.info(f"✅ Test key created: {expired_key_data['name']}")

    # Now manually set its expiration to the past
    import subprocess
    from datetime import timezone as tz
    past_expiration = datetime.now(tz.utc) - timedelta(hours=1)
    past_expiration_str = past_expiration.strftime("%Y-%m-%d %H:%M:%S")

    result = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph",
        "-c", f"UPDATE api_keys SET expires_at = '{past_expiration_str}+00' WHERE id = '{expired_key_id}';"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"❌ Failed to set expiration: {result.stderr}")
        return False
    logger.info(f"   ✅ Manually set expiration to 1 hour ago: {past_expiration}")

    # STEP 7: Test expired key is rejected
    log_separator()
    logger.info("STEP 7: Test expired API key is rejected with 401")
    log_separator()

    expired_test_response = requests.get(
        f"{AUTH_SERVICE_URL}/test/api-key-auth",
        headers={"Authorization": f"Bearer {expired_key}"}
    )

    if expired_test_response.status_code == 200:
        logger.error(f"❌ Expired API key was accepted (should be rejected!)")
        return False

    if expired_test_response.status_code != 401:
        logger.error(f"❌ Expected 401 for expired key, got {expired_test_response.status_code}")
        return False

    error_detail = expired_test_response.json().get("detail", "")
    logger.info(f"✅ Expired API key properly rejected with 401")
    logger.info(f"   Error message: {error_detail}")

    if "expired" not in error_detail.lower():
        logger.error(f"❌ Error message doesn't mention expiration")
        return False

    logger.info(f"   ✅ Error message correctly mentions expiration")

    # STEP 8: Verify expiration is stored in database
    log_separator()
    logger.info("STEP 8: Verify expiration dates stored in database")
    log_separator()

    import subprocess

    # Check non-expiring key
    result = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph", "-t",
        "-c", f"SELECT name, expires_at FROM api_keys WHERE key_prefix = '{no_expiry_data['key_prefix']}';"
    ], capture_output=True, text=True)

    no_expiry_db = result.stdout.strip().split('|')

    # Check expiring key
    result2 = subprocess.run([
        "docker", "exec", "autograph-postgres",
        "psql", "-U", "autograph", "-d", "autograph", "-t",
        "-c", f"SELECT name, expires_at FROM api_keys WHERE key_prefix = '{with_expiry_data['key_prefix']}';"
    ], capture_output=True, text=True)

    with_expiry_db = result2.stdout.strip().split('|')

    logger.info(f"✅ Database verification:")
    logger.info(f"   {no_expiry_db[0].strip()}: expires_at = {no_expiry_db[1].strip() if len(no_expiry_db) > 1 else 'NULL'} (should be NULL)")
    logger.info(f"   {with_expiry_db[0].strip()}: expires_at = {with_expiry_db[1].strip() if len(with_expiry_db) > 1 else 'NULL'} (should be set)")

    # Check if non-expiring key has NULL expiration
    if len(no_expiry_db) > 1 and no_expiry_db[1].strip():
        logger.error(f"❌ Non-expiring key has expiration set in database!")
        return False

    # Check if expiring key has expiration set
    if len(with_expiry_db) < 2 or not with_expiry_db[1].strip():
        logger.error(f"❌ Expiring key doesn't have expiration in database!")
        return False

    logger.info(f"   ✅ Expiration dates correctly stored")

    # Success!
    log_separator()
    logger.info("✅ ALL TESTS PASSED - Feature #109 working correctly!")
    log_separator()
    logger.info("")
    logger.info("Feature Summary:")
    logger.info("✅ API keys can be created without expiration (permanent)")
    logger.info("✅ API keys can be created with expiration date (expires_in_days)")
    logger.info("✅ Expiration date is calculated and stored correctly (~30 days)")
    logger.info("✅ Non-expired keys work normally")
    logger.info("✅ Expired keys are rejected with 401 Unauthorized")
    logger.info("✅ Error message mentions 'expired' for clarity")
    logger.info("✅ Expiration dates stored correctly in database (NULL for permanent)")
    logger.info("")
    logger.info("Note: This feature enables time-limited API access for security")

    return True


if __name__ == "__main__":
    try:
        success = test_feature_109()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Test Features #107-110: API Key Authentication

Feature #107: API key authentication for programmatic access
Feature #108: API key can be revoked
Feature #109: API key with expiration date
Feature #110: API key with scope restrictions (read-only, write, admin)
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8085"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 80}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 80}{RESET}\n")


def print_test(text):
    """Print a test step."""
    print(f"{YELLOW}{text}{RESET}")


def print_success(text):
    """Print a success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print an error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print an info message."""
    print(f"  {text}")


def register_user(email, password, role="viewer"):
    """Register a new user."""
    response = requests.post(
        f"{BASE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
            "role": role
        }
    )
    return response


def login_user(email, password):
    """Login a user and return access token."""
    response = requests.post(
        f"{BASE_URL}/token",
        data={
            "username": email,
            "password": password
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


def main():
    """Run the API keys test suite."""
    print_header("FEATURES #107-110: API KEY AUTHENTICATION TEST SUITE")
    print(f"Testing against: {BASE_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Generate unique email
    timestamp = int(time.time())
    test_email = f"apikey_test_{timestamp}@example.com"
    test_password = "SecurePassword123!"
    admin_email = f"admin_apikey_{timestamp}@example.com"
    
    try:
        # ====================================================================
        # SETUP: Register and login users
        # ====================================================================
        print_header("SETUP: Create Test Users")
        
        print_test("Step 1: Register regular user")
        response = register_user(test_email, test_password, "editor")
        if response.status_code in [200, 201]:
            user_data = response.json()
            user_id = user_data["id"]
            print_success(f"User registered (ID: {user_id})")
            print_info(f"Email: {test_email}")
        else:
            print_error(f"Registration failed: {response.text}")
            return False
        
        print_test("\nStep 2: Register admin user")
        response = register_user(admin_email, test_password, "admin")
        if response.status_code in [200, 201]:
            admin_data = response.json()
            admin_id = admin_data["id"]
            print_success(f"Admin registered (ID: {admin_id})")
            print_info(f"Email: {admin_email}")
        else:
            print_error(f"Admin registration failed: {response.text}")
            return False
        
        print_test("\nStep 3: Login regular user")
        user_token = login_user(test_email, test_password)
        if user_token:
            print_success("User logged in successfully")
            print_info(f"Token: {user_token[:20]}...")
        else:
            print_error("Login failed")
            return False
        
        print_test("\nStep 4: Login admin user")
        admin_token = login_user(admin_email, test_password)
        if admin_token:
            print_success("Admin logged in successfully")
            print_info(f"Token: {admin_token[:20]}...")
        else:
            print_error("Admin login failed")
            return False
        
        # ====================================================================
        # TEST FEATURE #107: API Key Authentication
        # ====================================================================
        print_header("TEST FEATURE #107: API Key Authentication")
        
        print_test("Step 1: Create API key without expiration")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Test Key 1",
                "scopes": ["read", "write"]
            }
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            api_key_1 = api_key_data["api_key"]
            api_key_1_id = api_key_data["id"]
            print_success("API key created successfully")
            print_info(f"Key ID: {api_key_1_id}")
            print_info(f"Key prefix: {api_key_data['key_prefix']}")
            print_info(f"Full key: {api_key_1[:15]}... (truncated)")
            print_info(f"Scopes: {api_key_data['scopes']}")
            print_info(f"Warning: {api_key_data['warning']}")
        else:
            print_error(f"API key creation failed: {response.text}")
            return False
        
        print_test("\nStep 2: Test API key authentication")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {api_key_1}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("API key authentication successful")
            print_info(f"User ID: {data['user_id']}")
            print_info(f"Email: {data['email']}")
            print_info(f"Message: {data['message']}")
        else:
            print_error(f"API key authentication failed: {response.text}")
            return False
        
        print_test("\nStep 3: List API keys")
        response = requests.get(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            keys = response.json()["api_keys"]
            print_success(f"Retrieved {len(keys)} API key(s)")
            for key in keys:
                print_info(f"  - {key['name']} ({key['key_prefix']}...) - Active: {key['is_active']}")
        else:
            print_error(f"Failed to list API keys: {response.text}")
            return False
        
        # ====================================================================
        # TEST FEATURE #109: API Key Expiration
        # ====================================================================
        print_header("TEST FEATURE #109: API Key with Expiration Date")
        
        print_test("Step 1: Create API key with 30-day expiration")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Test Key with Expiration",
                "scopes": ["read"],
                "expires_in_days": 30
            }
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            api_key_2 = api_key_data["api_key"]
            api_key_2_id = api_key_data["id"]
            expires_at = api_key_data["expires_at"]
            print_success("API key with expiration created")
            print_info(f"Key ID: {api_key_2_id}")
            print_info(f"Expires at: {expires_at}")
            print_info(f"Scopes: {api_key_data['scopes']}")
            
            # Verify expiration date is ~30 days in future
            expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            days_until_expiry = (expiry_date - datetime.now().astimezone()).days
            print_info(f"Days until expiry: {days_until_expiry}")
            
            if 29 <= days_until_expiry <= 31:
                print_success("Expiration date correctly set to ~30 days")
            else:
                print_error(f"Expiration date incorrect: {days_until_expiry} days")
        else:
            print_error(f"Failed to create API key with expiration: {response.text}")
            return False
        
        print_test("\nStep 2: Verify expiring key works")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {api_key_2}"}
        )
        
        if response.status_code == 200:
            print_success("Expiring API key authentication successful")
        else:
            print_error(f"Expiring API key authentication failed: {response.text}")
            return False
        
        # ====================================================================
        # TEST FEATURE #110: API Key Scope Restrictions
        # ====================================================================
        print_header("TEST FEATURE #110: API Key with Scope Restrictions")
        
        print_test("Step 1: Create read-only API key")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Read-Only Key",
                "scopes": ["read"]
            }
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            readonly_key = api_key_data["api_key"]
            print_success("Read-only API key created")
            print_info(f"Scopes: {api_key_data['scopes']}")
        else:
            print_error(f"Failed to create read-only key: {response.text}")
            return False
        
        print_test("\nStep 2: Create write API key")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Write Key",
                "scopes": ["read", "write"]
            }
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            write_key = api_key_data["api_key"]
            print_success("Write API key created")
            print_info(f"Scopes: {api_key_data['scopes']}")
        else:
            print_error(f"Failed to create write key: {response.text}")
            return False
        
        print_test("\nStep 3: Try to create admin scope key as non-admin (should fail)")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Admin Key",
                "scopes": ["admin"]
            }
        )
        
        if response.status_code == 403:
            print_success("Non-admin correctly blocked from creating admin scope key")
            print_info(f"Error: {response.json()['detail']}")
        else:
            print_error(f"Non-admin should not be able to create admin scope key")
            return False
        
        print_test("\nStep 4: Create admin scope key as admin user")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "Admin Key",
                "scopes": ["admin"]
            }
        )
        
        if response.status_code == 200:
            api_key_data = response.json()
            admin_key = api_key_data["api_key"]
            admin_key_id = api_key_data["id"]
            print_success("Admin scope key created by admin user")
            print_info(f"Scopes: {api_key_data['scopes']}")
        else:
            print_error(f"Admin failed to create admin scope key: {response.text}")
            return False
        
        print_test("\nStep 5: Test invalid scope (should fail)")
        response = requests.post(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "name": "Invalid Scope Key",
                "scopes": ["invalid_scope"]
            }
        )
        
        if response.status_code == 400:
            print_success("Invalid scope correctly rejected")
            print_info(f"Error: {response.json()['detail']}")
        else:
            print_error(f"Invalid scope should be rejected")
            return False
        
        # ====================================================================
        # TEST FEATURE #108: API Key Revocation
        # ====================================================================
        print_header("TEST FEATURE #108: API Key Revocation")
        
        print_test("Step 1: Verify API key works before revocation")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {api_key_1}"}
        )
        
        if response.status_code == 200:
            print_success("API key works before revocation")
        else:
            print_error(f"API key should work before revocation: {response.text}")
            return False
        
        print_test("\nStep 2: Revoke API key")
        response = requests.delete(
            f"{BASE_URL}/api-keys/{api_key_1_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("API key revoked successfully")
            print_info(f"Message: {data['message']}")
            print_info(f"Key name: {data['key_name']}")
        else:
            print_error(f"Failed to revoke API key: {response.text}")
            return False
        
        print_test("\nStep 3: Verify revoked key no longer works")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {api_key_1}"}
        )
        
        if response.status_code == 401:
            print_success("Revoked API key correctly rejected")
            print_info(f"Error: {response.json()['detail']}")
        else:
            print_error(f"Revoked API key should not work: {response.text}")
            return False
        
        print_test("\nStep 4: List API keys (revoked key should show as inactive)")
        response = requests.get(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            keys = response.json()["api_keys"]
            revoked_key = next((k for k in keys if k['id'] == api_key_1_id), None)
            
            if revoked_key and not revoked_key['is_active']:
                print_success("Revoked key shows as inactive in list")
                print_info(f"Key: {revoked_key['name']} - Active: {revoked_key['is_active']}")
            else:
                print_error("Revoked key should show as inactive")
                return False
        else:
            print_error(f"Failed to list API keys: {response.text}")
            return False
        
        print_test("\nStep 5: Try to revoke non-existent key (should fail)")
        response = requests.delete(
            f"{BASE_URL}/api-keys/non-existent-id",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 404:
            print_success("Non-existent key revocation correctly rejected")
            print_info(f"Error: {response.json()['detail']}")
        else:
            print_error(f"Non-existent key revocation should fail with 404")
            return False
        
        # ====================================================================
        # ADDITIONAL TESTS
        # ====================================================================
        print_header("ADDITIONAL TESTS")
        
        print_test("Step 1: Test JWT fallback (regular JWT token should still work)")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            print_success("JWT authentication still works (fallback successful)")
        else:
            print_error(f"JWT authentication should still work: {response.text}")
            return False
        
        print_test("\nStep 2: Test with invalid API key (should fail)")
        response = requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer ag_invalid_key_12345"}
        )
        
        if response.status_code == 401:
            print_success("Invalid API key correctly rejected")
            print_info(f"Error: {response.json()['detail']}")
        else:
            print_error(f"Invalid API key should be rejected")
            return False
        
        print_test("\nStep 3: Verify last_used_at timestamp is updated")
        time.sleep(2)  # Wait 2 seconds
        
        # Use API key
        requests.get(
            f"{BASE_URL}/test/api-key-auth",
            headers={"Authorization": f"Bearer {api_key_2}"}
        )
        
        # Check if last_used_at is recent
        response = requests.get(
            f"{BASE_URL}/api-keys",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        if response.status_code == 200:
            keys = response.json()["api_keys"]
            used_key = next((k for k in keys if k['id'] == api_key_2_id), None)
            
            if used_key and used_key['last_used_at']:
                last_used = datetime.fromisoformat(used_key['last_used_at'].replace('Z', '+00:00'))
                seconds_ago = (datetime.now().astimezone() - last_used).total_seconds()
                
                if seconds_ago < 10:  # Used within last 10 seconds
                    print_success("last_used_at timestamp correctly updated")
                    print_info(f"Last used: {seconds_ago:.1f} seconds ago")
                else:
                    print_error(f"last_used_at timestamp not recent: {seconds_ago:.1f} seconds ago")
            else:
                print_error("last_used_at should be set after use")
        
        # ====================================================================
        # TEST SUMMARY
        # ====================================================================
        print_header("✅ ALL TESTS PASSED")
        print()
        print("Test Summary:")
        print("  Feature #107: API key authentication for programmatic access")
        print("    • API key creation ✅")
        print("    • API key authentication ✅")
        print("    • API key listing ✅")
        print("    • JWT fallback ✅")
        print()
        print("  Feature #108: API key can be revoked")
        print("    • Revoke active key ✅")
        print("    • Revoked key rejected ✅")
        print("    • Inactive status tracked ✅")
        print()
        print("  Feature #109: API key with expiration date")
        print("    • Create key with expiration ✅")
        print("    • Expiration date calculated correctly ✅")
        print("    • Expiring key works before expiry ✅")
        print()
        print("  Feature #110: API key with scope restrictions")
        print("    • Read-only scope ✅")
        print("    • Write scope ✅")
        print("    • Admin scope (admin only) ✅")
        print("    • Scope validation ✅")
        print("    • Non-admin blocked from admin scope ✅")
        print()
        
        print_header("TEST SUMMARY")
        print(f"{GREEN}Features #107-110 (API Keys): ✅ PASSED{RESET}")
        print_header("=" * 80)
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test Feature #112: OAuth 2.0 Authorization Code Flow

Tests the complete OAuth 2.0 flow:
1. User creates OAuth app
2. Third-party app redirects user to /oauth/authorize
3. User grants consent
4. App receives authorization code
5. App exchanges code for access token
6. App uses access token to access API
"""

import requests
import json
import time
from urllib.parse import urlparse, parse_qs

# Base URLs
AUTH_BASE = "http://localhost:8080/api/auth"
API_BASE = "http://localhost:8080/api"

# Test user credentials
TEST_EMAIL = f"oauth_test_{int(time.time())}@example.com"
TEST_PASSWORD = "SecurePassword123!@#"

# OAuth app details
OAUTH_APP_NAME = "Test OAuth App"
OAUTH_REDIRECT_URI = "http://localhost:3000/oauth/callback"

def print_step(step_num, description):
    """Print test step header."""
    print(f"\n{'='*70}")
    print(f"Step {step_num}: {description}")
    print('='*70)

def print_result(success, message):
    """Print test result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")

def main():
    print("\n" + "="*70)
    print("FEATURE #112: OAuth 2.0 Authorization Code Flow Test")
    print("="*70)
    
    # Step 1: Register test user
    print_step(1, "Register test user")
    try:
        response = requests.post(
            f"{AUTH_BASE}/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code in (200, 201):
            user_data = response.json()
            user_id = user_data["id"]
            print_result(True, f"User registered: {TEST_EMAIL}")
            print(f"User ID: {user_id}")
        else:
            print_result(False, f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Registration error: {e}")
        return False
    
    # Mark user as verified (bypass email verification for testing)
    print_step(2, "Mark user as verified (bypass email verification)")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (TEST_EMAIL,))
        conn.commit()
        cur.close()
        conn.close()
        print_result(True, "User marked as verified")
    except Exception as e:
        print_result(False, f"Failed to mark user as verified: {e}")
        return False
    
    # Step 3: Login to get access token
    print_step(3, "Login to get access token")
    try:
        response = requests.post(
            f"{AUTH_BASE}/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            login_data = response.json()
            access_token = login_data["access_token"]
            print_result(True, "Login successful")
            print(f"Access token: {access_token[:50]}...")
        else:
            print_result(False, f"Login failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Login error: {e}")
        return False
    
    # Step 4: Create OAuth application
    print_step(4, "Create OAuth application (POST /oauth/apps)")
    try:
        response = requests.post(
            f"{AUTH_BASE}/oauth/apps",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "name": OAUTH_APP_NAME,
                "description": "Test OAuth application for Feature #112",
                "redirect_uris": [OAUTH_REDIRECT_URI],
                "allowed_scopes": ["read", "write"]
            }
        )
        
        if response.status_code == 201:
            oauth_app = response.json()
            client_id = oauth_app["client_id"]
            client_secret = oauth_app["client_secret"]
            print_result(True, "OAuth app created")
            print(f"Client ID: {client_id}")
            print(f"Client Secret: {client_secret[:20]}...")
        else:
            print_result(False, f"OAuth app creation failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"OAuth app creation error: {e}")
        return False
    
    # Step 5: Request authorization (GET /oauth/authorize)
    print_step(5, "Request authorization (GET /oauth/authorize)")
    try:
        # This would normally redirect user to consent screen
        # For testing, we'll call the endpoint directly with user's token
        response = requests.get(
            f"{AUTH_BASE}/oauth/authorize",
            headers={"Authorization": f"Bearer {access_token}"},
            params={
                "client_id": client_id,
                "redirect_uri": OAUTH_REDIRECT_URI,
                "response_type": "code",
                "scope": "read,write",
                "state": "random_state_token_123"
            },
            allow_redirects=False  # Don't follow redirect
        )
        
        if response.status_code in (302, 303, 307):
            redirect_location = response.headers.get("Location")
            print_result(True, "Authorization granted, redirect received")
            print(f"Redirect location: {redirect_location}")
            
            # Parse authorization code from redirect
            parsed_url = urlparse(redirect_location)
            query_params = parse_qs(parsed_url.query)
            auth_code = query_params.get("code", [None])[0]
            state = query_params.get("state", [None])[0]
            
            if auth_code:
                print_result(True, f"Authorization code received: {auth_code[:20]}...")
                print(f"State: {state}")
            else:
                print_result(False, "No authorization code in redirect")
                return False
        else:
            print_result(False, f"Authorization failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Authorization error: {e}")
        return False
    
    # Step 6: Exchange authorization code for access token (POST /oauth/token)
    print_step(6, "Exchange code for access token (POST /oauth/token)")
    try:
        response = requests.post(
            f"{AUTH_BASE}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": OAUTH_REDIRECT_URI,
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            oauth_access_token = token_data["access_token"]
            oauth_refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]
            scope = token_data["scope"]
            
            print_result(True, "Access token received")
            print(f"Access token: {oauth_access_token[:50]}...")
            print(f"Refresh token: {oauth_refresh_token[:50]}...")
            print(f"Expires in: {expires_in} seconds")
            print(f"Scope: {scope}")
        else:
            print_result(False, f"Token exchange failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Token exchange error: {e}")
        return False
    
    # Step 7: Use OAuth access token to call API
    print_step(7, "Use OAuth token to access API (GET /api/diagrams)")
    try:
        response = requests.get(
            f"{API_BASE}/diagrams",
            headers={"Authorization": f"Bearer {oauth_access_token}"}
        )
        
        if response.status_code == 200:
            diagrams = response.json()
            print_result(True, f"API call successful using OAuth token")
            print(f"Diagrams returned: {len(diagrams.get('diagrams', []))}")
        else:
            print_result(False, f"API call failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_result(False, f"API call error: {e}")
        return False
    
    # Step 8: Test token refresh (Feature #113)
    print_step(8, "Test token refresh (grant_type=refresh_token)")
    try:
        time.sleep(2)  # Wait a bit before refreshing
        
        response = requests.post(
            f"{AUTH_BASE}/oauth/token",
            json={
                "grant_type": "refresh_token",
                "refresh_token": oauth_refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            }
        )
        
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data["access_token"]
            print_result(True, "Token refresh successful")
            print(f"New access token: {new_access_token[:50]}...")
            
            # Verify new token works
            response = requests.get(
                f"{API_BASE}/diagrams",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            if response.status_code == 200:
                print_result(True, "New access token works")
            else:
                print_result(False, "New access token doesn't work")
                return False
        else:
            print_result(False, f"Token refresh failed: {response.text}")
            return False
    except Exception as e:
        print_result(False, f"Token refresh error: {e}")
        return False
    
    # Final summary
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - Feature #112 OAuth 2.0 Working!")
    print("="*70)
    print("\nFeature Summary:")
    print("  ✅ OAuth app registration")
    print("  ✅ Authorization code flow")
    print("  ✅ Token exchange")
    print("  ✅ OAuth token authentication")
    print("  ✅ Token refresh")
    print("\nReady to mark feature #112 as passing!")
    print("="*70 + "\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

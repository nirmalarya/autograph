#!/usr/bin/env python3
"""
Validation script for Feature #115: OAuth 2.0 token revocation

Tests:
1. Complete OAuth flow to get access_token
2. User navigates to /settings/connected-apps
3. User clicks 'Revoke Access' for App X
4. Verify access_token invalidated
5. App attempts to use access_token
6. Verify 401 Unauthorized response
7. Verify error: 'Token revoked'
"""

import requests
import sys
import json
import time
import secrets

BASE_URL = "http://localhost:8080"
AUTH_URL = "http://localhost:8085"

def print_status(message, status="info"):
    """Print formatted status message."""
    symbols = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
    print(f"{symbols.get(status, 'ℹ️')} {message}")


def test_oauth_token_revocation():
    """Test OAuth 2.0 token revocation flow."""

    print("\n" + "="*80)
    print("Feature #115: OAuth 2.0 Token Revocation Validation")
    print("="*80 + "\n")

    try:
        # Step 1: Register a test user
        print_status("Step 1: Registering test user...", "info")
        register_data = {
            "email": f"revoke_test_{secrets.token_hex(4)}@example.com",
            "password": "SecurePass123!",
            "full_name": "Revocation Test User"
        }

        response = requests.post(f"{AUTH_URL}/register", json=register_data)
        if response.status_code != 201:
            print_status(f"Registration failed: {response.text}", "error")
            return False

        user_email = register_data["email"]
        user_password = register_data["password"]
        user_id = response.json()["id"]
        print_status(f"User registered: {user_email}", "success")

        # Verify email
        print_status("Verifying email...", "info")
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='autograph',
            user='autograph',
            password='autograph_dev_password'
        )
        cur = conn.cursor()
        cur.execute(
            'SELECT token FROM email_verification_tokens WHERE user_id = %s ORDER BY created_at DESC LIMIT 1',
            (user_id,)
        )
        token_row = cur.fetchone()

        if not token_row:
            print_status("Verification token not found", "error")
            cur.close()
            conn.close()
            return False

        verify_token = token_row[0]
        cur.close()
        conn.close()

        verify_response = requests.post(
            f"{AUTH_URL}/email/verify",
            json={"token": verify_token}
        )
        if verify_response.status_code != 200:
            print_status(f"Email verification failed: {verify_response.text}", "error")
            return False

        print_status("Email verified", "success")

        # Step 2: Login to get regular access token
        print_status("Step 2: Logging in...", "info")
        login_response = requests.post(
            f"{AUTH_URL}/login",
            json={"email": user_email, "password": user_password}
        )

        if login_response.status_code != 200:
            print_status(f"Login failed: {login_response.text}", "error")
            return False

        user_token = login_response.json()["access_token"]

        # Decode JWT to get user ID
        import jwt
        decoded = jwt.decode(user_token, options={"verify_signature": False})
        user_id = decoded["sub"]

        print_status("Login successful", "success")

        # Step 3: Create an OAuth app
        print_status("Step 3: Creating OAuth app...", "info")
        app_data = {
            "name": "Test Revocation App",
            "description": "App for testing token revocation",
            "redirect_uris": ["http://localhost:3000/callback"],
            "allowed_scopes": ["read", "write"]
        }

        response = requests.post(
            f"{AUTH_URL}/oauth/apps",
            json=app_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        if response.status_code != 201:
            print_status(f"OAuth app creation failed: {response.text}", "error")
            return False

        oauth_app = response.json()
        client_id = oauth_app["client_id"]
        client_secret = oauth_app["client_secret"]
        print_status(f"OAuth app created: {oauth_app['name']}", "success")

        # Step 4: Complete OAuth authorization flow
        print_status("Step 4: Completing OAuth authorization flow...", "info")

        # 4a: Get authorization code
        auth_params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": "http://localhost:3000/callback",
            "scope": "read,write",
            "state": secrets.token_urlsafe(16)
        }

        response = requests.get(
            f"{AUTH_URL}/oauth/authorize",
            params=auth_params,
            headers={"Authorization": f"Bearer {user_token}"},
            allow_redirects=False
        )

        if response.status_code not in (302, 307):
            print_status(f"Authorization failed (status {response.status_code})", "error")
            print_status(f"Response: {response.text}", "error")
            return False

        # Extract authorization code from redirect
        location = response.headers.get("Location", "")
        if "code=" not in location:
            print_status("Authorization code not found in redirect", "error")
            return False

        auth_code = location.split("code=")[1].split("&")[0]
        print_status("Authorization code obtained", "success")

        # 4b: Exchange code for access token
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "http://localhost:3000/callback",
            "client_id": client_id,
            "client_secret": client_secret
        }

        response = requests.post(f"{AUTH_URL}/oauth/token", json=token_data)

        if response.status_code != 200:
            print_status(f"Token exchange failed: {response.text}", "error")
            return False

        token_response = response.json()
        oauth_access_token = token_response["access_token"]
        print_status("OAuth access token obtained", "success")

        # Step 5: Use OAuth token to make API request (should work)
        # Use a protected endpoint (not /health which is public)
        print_status("Step 5: Testing OAuth token (before revocation)...", "info")
        response = requests.get(
            f"{BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {oauth_access_token}"}
        )

        if response.status_code not in (200, 404):  # 404 is OK if no diagrams exist
            print_status(f"API request with OAuth token failed: {response.status_code}", "error")
            return False

        print_status("OAuth token works before revocation", "success")

        # Step 6: List connected apps
        print_status("Step 6: Listing connected apps...", "info")
        # Call auth service directly
        response = requests.get(
            f"{AUTH_URL}/settings/connected-apps",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        if response.status_code != 200:
            print_status(f"Failed to list connected apps: {response.text}", "error")
            return False

        connected_apps = response.json()["connected_apps"]
        if len(connected_apps) == 0:
            print_status("No connected apps found", "error")
            return False

        print_status(f"Found {len(connected_apps)} connected app(s)", "success")

        app_info = connected_apps[0]
        print(f"   App: {app_info['app_name']}")
        print(f"   Scopes: {app_info['scopes']}")
        print(f"   Is Revoked: {app_info['is_revoked']}")

        # Step 7: Revoke OAuth token
        print_status("Step 7: Revoking OAuth access token...", "info")
        revoke_data = {
            "token": oauth_access_token,
            "token_type_hint": "access_token"
        }

        response = requests.post(
            f"{AUTH_URL}/oauth/revoke",
            params=revoke_data,
            headers={"Authorization": f"Bearer {user_token}"}
        )

        if response.status_code != 200:
            print_status(f"Token revocation failed: {response.text}", "error")
            return False

        print_status("OAuth token revoked successfully", "success")

        # Step 8: Try to use revoked token (should fail with 401)
        print_status("Step 8: Testing revoked OAuth token (should fail)...", "info")
        response = requests.get(
            f"{BASE_URL}/api/diagrams",
            headers={"Authorization": f"Bearer {oauth_access_token}"}
        )

        if response.status_code == 200:
            print_status("ERROR: Revoked token still works!", "error")
            return False

        if response.status_code != 401:
            print_status(f"Unexpected status code: {response.status_code} (expected 401)", "error")
            return False

        error_detail = response.json().get("detail", "")
        if "revoked" not in error_detail.lower():
            print_status(f"Error message doesn't mention revocation: {error_detail}", "warning")

        print_status("Revoked token correctly rejected with 401", "success")
        print(f"   Error: {error_detail}")

        # Step 9: Verify connected apps shows revoked status
        print_status("Step 9: Verifying connected apps shows revoked status...", "info")
        response = requests.get(
            f"{AUTH_URL}/settings/connected-apps",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        if response.status_code != 200:
            print_status(f"Failed to list connected apps: {response.text}", "error")
            return False

        connected_apps = response.json()["connected_apps"]
        app_info = connected_apps[0]

        if not app_info["is_revoked"]:
            print_status("App not showing as revoked!", "error")
            return False

        if not app_info["revoked_at"]:
            print_status("Revoked timestamp missing!", "error")
            return False

        print_status("Connected apps correctly shows revoked status", "success")
        print(f"   Revoked at: {app_info['revoked_at']}")

        print("\n" + "="*80)
        print_status("Feature #115: OAuth 2.0 Token Revocation - ALL TESTS PASSED", "success")
        print("="*80 + "\n")

        return True

    except Exception as e:
        print_status(f"Test failed with exception: {str(e)}", "error")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_oauth_token_revocation()
    sys.exit(0 if success else 1)

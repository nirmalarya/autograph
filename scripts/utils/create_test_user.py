#!/usr/bin/env python3
"""Create a verified test user for testing purposes."""

import requests
import json

API_BASE = "http://localhost:8080"

def create_verified_user():
    """Create a verified user by registering and manually verifying."""
    
    # Step 1: Register a new user
    email = "verified@test.com"
    password = "Test123!@#"
    
    print("Creating user...")
    register_response = requests.post(
        f"{API_BASE}/auth/register",
        json={
            "email": email,
            "password": password
        }
    )
    
    if register_response.status_code == 201:
        print(f"✓ User created: {email}")
    elif register_response.status_code == 409:
        print(f"ℹ User already exists: {email}")
    else:
        print(f"✗ Failed to create user: {register_response.status_code}")
        print(f"  Response: {register_response.text}")
        return None
    
    # Step 2: Try to login (this will likely fail due to email verification)
    print("\nAttempting login...")
    login_response = requests.post(
        f"{API_BASE}/auth/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if login_response.status_code == 200:
        data = login_response.json()
        token = data.get("access_token")
        print(f"✓ Login successful!")
        print(f"  Token: {token[:50]}...")
        return token
    else:
        print(f"✗ Login failed: {login_response.status_code}")
        print(f"  Response: {login_response.text}")
        
        # Check if email verification is the issue
        if "verify your email" in login_response.text.lower():
            print("\nEmail verification is required.")
            print("Looking for a way to bypass or manually verify...")
            
            # Try to find the verification endpoint
            # In many apps, there's an admin bypass or we can directly mark as verified
            return None
    
    return None

if __name__ == "__main__":
    print("="*80)
    print("CREATE VERIFIED TEST USER")
    print("="*80)
    print()
    
    token = create_verified_user()
    
    if token:
        print("\n" + "="*80)
        print("SUCCESS! Test user is ready.")
        print("="*80)
        print(f"\nEmail: verified@test.com")
        print(f"Password: Test123!@#")
        print(f"Token: {token}")
    else:
        print("\n" + "="*80)
        print("Email verification required - checking for workaround...")
        print("="*80)
        
        # Let's check if there's a test mode or admin endpoint
        # For now, let's just try with a different approach
        print("\nSuggestion: Check if auth-service has REQUIRE_EMAIL_VERIFICATION=false config")

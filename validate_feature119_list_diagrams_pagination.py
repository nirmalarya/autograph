#!/usr/bin/env python3
"""
Feature #119 Validation: List user's diagrams with pagination

This script validates:
1. Create 25 diagrams
2. Navigate to /dashboard (GET /api/diagrams)
3. Verify first 20 diagrams displayed
4. Verify pagination controls shown (metadata)
5. Click 'Next Page' (page=2)
6. Verify remaining 5 diagrams displayed
7. Verify page 2 of 2 indicator
8. Click 'Previous Page' (page=1)
9. Verify back to first 20 diagrams
"""

import requests
import json
import sys
import time
import psycopg2
import base64
from typing import Dict, List, Any

# Configuration
API_BASE_URL = "http://localhost:8080"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def print_step(step_num: int, description: str):
    """Print test step header."""
    print(f"\n{'='*80}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*80}")

def register_and_login() -> tuple[str, str]:
    """Register a new user and login to get tokens."""
    print_step(1, "Register user and login")

    # Generate unique email
    timestamp = int(time.time())
    email = f"pagination_test_{timestamp}@example.com"
    password = "SecurePass123!@#"

    # Register
    register_data = {
        "email": email,
        "password": password,
        "full_name": "Pagination Test User"
    }

    print(f"  → Registering user: {email}")
    response = requests.post(
        f"{API_BASE_URL}/api/auth/register",
        json=register_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 201:
        print(f"  ✗ Registration failed: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

    print(f"  ✓ User registered successfully")

    # Mark user as verified in database (skip email verification for test)
    print(f"  → Marking user as verified in database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓ User marked as verified")
    except Exception as e:
        print(f"  ✗ Failed to mark user as verified: {e}")
        sys.exit(1)

    # Login
    login_data = {
        "email": email,
        "password": password
    }

    print(f"  → Logging in...")
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code != 200:
        print(f"  ✗ Login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

    auth_data = response.json()
    access_token = auth_data.get("access_token")

    if not access_token:
        print(f"  ✗ No access token in response")
        print(f"  Response: {json.dumps(auth_data, indent=2)}")
        sys.exit(1)

    # Decode JWT to get user_id from 'sub' claim
    try:
        # JWT format: header.payload.signature
        payload_b64 = access_token.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        user_id = payload.get('sub')
        if not user_id:
            print(f"  ✗ No 'sub' claim in JWT token")
            print(f"  Payload: {json.dumps(payload, indent=2)}")
            sys.exit(1)
    except Exception as e:
        print(f"  ✗ Failed to decode JWT token: {e}")
        sys.exit(1)

    print(f"  ✓ Login successful")
    print(f"  ✓ User ID: {user_id}")
    print(f"  ✓ Access token obtained: {access_token[:20]}...")

    return access_token, user_id

def create_diagrams(access_token: str, user_id: str, count: int) -> List[str]:
    """Create multiple diagrams and return their IDs."""
    print_step(2, f"Create {count} diagrams")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id,
        "Content-Type": "application/json"
    }

    diagram_ids = []

    for i in range(1, count + 1):
        diagram_data = {
            "title": f"Test Diagram {i:02d}",
            "file_type": "canvas",
            "canvas_data": {
                "nodes": [
                    {
                        "id": f"node_{i}",
                        "type": "rectangle",
                        "x": 100,
                        "y": 100,
                        "width": 150,
                        "height": 80,
                        "text": f"Diagram {i}"
                    }
                ],
                "edges": []
            }
        }

        response = requests.post(
            f"{API_BASE_URL}/api/diagrams",
            json=diagram_data,
            headers=headers
        )

        # Accept both 200 and 201 as success
        if response.status_code not in [200, 201]:
            print(f"  ✗ Failed to create diagram {i}: {response.status_code}")
            print(f"  Response: {response.text}")
            sys.exit(1)

        diagram = response.json()
        diagram_id = diagram.get("id")
        diagram_ids.append(diagram_id)

        if i % 5 == 0:
            print(f"  ✓ Created {i}/{count} diagrams...")

    print(f"  ✓ All {count} diagrams created successfully")
    print(f"  ✓ Diagram IDs: {diagram_ids[:3]}... (showing first 3)")

    return diagram_ids

def list_diagrams_page(access_token: str, user_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """List diagrams with pagination."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }

    params = {
        "page": page,
        "page_size": page_size
    }

    response = requests.get(
        f"{API_BASE_URL}/api/diagrams",
        params=params,
        headers=headers
    )

    if response.status_code != 200:
        print(f"  ✗ Failed to list diagrams: {response.status_code}")
        print(f"  Response: {response.text}")
        sys.exit(1)

    return response.json()

def test_first_page(access_token: str, user_id: str):
    """Test first page shows 20 diagrams with correct pagination metadata."""
    print_step(3, "Navigate to /dashboard (GET /api/diagrams - page 1)")

    result = list_diagrams_page(access_token, user_id, page=1, page_size=20)

    # Verify response structure
    print(f"  → Verifying response structure...")
    required_fields = ['diagrams', 'total', 'page', 'page_size', 'total_pages', 'has_next', 'has_prev']
    for field in required_fields:
        if field not in result:
            print(f"  ✗ Missing field in response: {field}")
            sys.exit(1)
    print(f"  ✓ Response has all required fields")

    # Verify first 20 diagrams displayed
    print(f"  → Verifying first 20 diagrams displayed...")
    diagrams = result['diagrams']
    if len(diagrams) != 20:
        print(f"  ✗ Expected 20 diagrams, got {len(diagrams)}")
        sys.exit(1)
    print(f"  ✓ First page shows 20 diagrams")

    # Verify pagination metadata
    print(f"  → Verifying pagination metadata...")
    total = result['total']
    page = result['page']
    page_size = result['page_size']
    total_pages = result['total_pages']
    has_next = result['has_next']
    has_prev = result['has_prev']

    print(f"    Total diagrams: {total}")
    print(f"    Current page: {page}")
    print(f"    Page size: {page_size}")
    print(f"    Total pages: {total_pages}")
    print(f"    Has next: {has_next}")
    print(f"    Has prev: {has_prev}")

    # Verify values
    if total != 25:
        print(f"  ✗ Expected total=25, got {total}")
        sys.exit(1)

    if page != 1:
        print(f"  ✗ Expected page=1, got {page}")
        sys.exit(1)

    if page_size != 20:
        print(f"  ✗ Expected page_size=20, got {page_size}")
        sys.exit(1)

    if total_pages != 2:
        print(f"  ✗ Expected total_pages=2, got {total_pages}")
        sys.exit(1)

    if not has_next:
        print(f"  ✗ Expected has_next=True, got {has_next}")
        sys.exit(1)

    if has_prev:
        print(f"  ✗ Expected has_prev=False, got {has_prev}")
        sys.exit(1)

    print(f"  ✓ Pagination metadata is correct for page 1")

    # Verify diagram structure
    print(f"  → Verifying diagram structure...")
    first_diagram = diagrams[0]
    required_diagram_fields = ['id', 'title', 'file_type', 'owner_id', 'created_at', 'updated_at']
    for field in required_diagram_fields:
        if field not in first_diagram:
            print(f"  ✗ Missing field in diagram: {field}")
            sys.exit(1)
    print(f"  ✓ Diagrams have correct structure")

    print(f"\n  ✓ Page 1 validation successful!")
    return result

def test_second_page(access_token: str, user_id: str):
    """Test second page shows remaining 5 diagrams."""
    print_step(4, "Click 'Next Page' (GET /api/diagrams?page=2)")

    result = list_diagrams_page(access_token, user_id, page=2, page_size=20)

    # Verify remaining 5 diagrams displayed
    print(f"  → Verifying remaining 5 diagrams displayed...")
    diagrams = result['diagrams']
    if len(diagrams) != 5:
        print(f"  ✗ Expected 5 diagrams, got {len(diagrams)}")
        sys.exit(1)
    print(f"  ✓ Second page shows 5 diagrams")

    # Verify pagination metadata for page 2
    print(f"  → Verifying pagination metadata for page 2...")
    total = result['total']
    page = result['page']
    page_size = result['page_size']
    total_pages = result['total_pages']
    has_next = result['has_next']
    has_prev = result['has_prev']

    print(f"    Total diagrams: {total}")
    print(f"    Current page: {page}")
    print(f"    Page size: {page_size}")
    print(f"    Total pages: {total_pages}")
    print(f"    Has next: {has_next}")
    print(f"    Has prev: {has_prev}")

    # Verify values
    if total != 25:
        print(f"  ✗ Expected total=25, got {total}")
        sys.exit(1)

    if page != 2:
        print(f"  ✗ Expected page=2, got {page}")
        sys.exit(1)

    if page_size != 20:
        print(f"  ✗ Expected page_size=20, got {page_size}")
        sys.exit(1)

    if total_pages != 2:
        print(f"  ✗ Expected total_pages=2, got {total_pages}")
        sys.exit(1)

    if has_next:
        print(f"  ✗ Expected has_next=False, got {has_next}")
        sys.exit(1)

    if not has_prev:
        print(f"  ✗ Expected has_prev=True, got {has_prev}")
        sys.exit(1)

    print(f"  ✓ Pagination metadata is correct for page 2")
    print(f"  ✓ Page 2 of 2 indicator verified (page=2, total_pages=2)")

    print(f"\n  ✓ Page 2 validation successful!")
    return result

def test_back_to_first_page(access_token: str, user_id: str):
    """Test going back to first page."""
    print_step(5, "Click 'Previous Page' (GET /api/diagrams?page=1)")

    result = list_diagrams_page(access_token, user_id, page=1, page_size=20)

    # Verify back to 20 diagrams
    print(f"  → Verifying back to 20 diagrams...")
    diagrams = result['diagrams']
    if len(diagrams) != 20:
        print(f"  ✗ Expected 20 diagrams, got {len(diagrams)}")
        sys.exit(1)
    print(f"  ✓ Back to first page with 20 diagrams")

    # Verify pagination metadata
    print(f"  → Verifying pagination metadata...")
    page = result['page']
    has_next = result['has_next']
    has_prev = result['has_prev']

    if page != 1:
        print(f"  ✗ Expected page=1, got {page}")
        sys.exit(1)

    if not has_next:
        print(f"  ✗ Expected has_next=True, got {has_next}")
        sys.exit(1)

    if has_prev:
        print(f"  ✗ Expected has_prev=False, got {has_prev}")
        sys.exit(1)

    print(f"  ✓ Pagination metadata is correct for page 1")
    print(f"\n  ✓ Previous page navigation successful!")
    return result

def main():
    """Main validation function."""
    print("="*80)
    print("Feature #119 Validation: List user's diagrams with pagination")
    print("="*80)

    try:
        # Step 1: Register and login
        access_token, user_id = register_and_login()

        # Step 2: Create 25 diagrams
        diagram_ids = create_diagrams(access_token, user_id, count=25)

        # Step 3: Test first page (20 diagrams)
        page1_result = test_first_page(access_token, user_id)

        # Step 4: Test second page (5 diagrams)
        page2_result = test_second_page(access_token, user_id)

        # Step 5: Test back to first page
        back_to_page1_result = test_back_to_first_page(access_token, user_id)

        # All tests passed
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print("✓ Feature #119: List user's diagrams with pagination")
        print("")
        print("All test steps passed:")
        print("  ✓ Step 1: Created 25 diagrams")
        print("  ✓ Step 2: Navigate to /dashboard (page 1)")
        print("  ✓ Step 3: Verified first 20 diagrams displayed")
        print("  ✓ Step 4: Verified pagination controls shown")
        print("  ✓ Step 5: Click 'Next Page' (page 2)")
        print("  ✓ Step 6: Verified remaining 5 diagrams displayed")
        print("  ✓ Step 7: Verified page 2 of 2 indicator")
        print("  ✓ Step 8: Click 'Previous Page' (page 1)")
        print("  ✓ Step 9: Verified back to first 20 diagrams")
        print("")
        print("Pagination implementation details:")
        print(f"  • Total diagrams: 25")
        print(f"  • Page size: 20")
        print(f"  • Total pages: 2")
        print(f"  • Page 1: 20 diagrams (has_next=True, has_prev=False)")
        print(f"  • Page 2: 5 diagrams (has_next=False, has_prev=True)")
        print("")
        print("✅ Feature #119 is PASSING")
        print("="*80)

        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

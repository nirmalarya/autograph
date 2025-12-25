#!/usr/bin/env python3
"""
Feature #121 Validation: List diagrams with search by title

Tests:
1. Create diagrams with specific titles
2. Search by partial title (e.g., 'Architecture')
3. Search by specific word (e.g., 'AWS')
4. Clear search and verify all diagrams returned
5. Verify search is case-insensitive
6. Verify search accuracy (no false positives/negatives)
"""

import requests
import sys
import time
import json
import psycopg2
import base64

# Configuration
API_GATEWAY = "http://localhost:8080"
DIAGRAM_SERVICE = f"{API_GATEWAY}/api/diagrams"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}

def print_step(step_num, description):
    """Print a test step."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def register_and_login():
    """Register a user and login to get auth token."""
    print_step(1, "Register user and login")

    # Unique email for this test
    email = f"search_test_{int(time.time())}@example.com"
    password = "SecurePass123!"

    # Register
    print(f"  → Registering user: {email}")
    response = requests.post(
        f"{API_GATEWAY}/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Search Test User"
        }
    )

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None

    print(f"✅ Registered user: {email}")

    # Mark user as verified in database
    print(f"  → Marking user as verified...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = TRUE WHERE email = %s", (email,))
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ User marked as verified")
    except Exception as e:
        print(f"❌ Failed to mark user as verified: {e}")
        return None, None

    # Login
    print(f"  → Logging in...")
    response = requests.post(
        f"{API_GATEWAY}/api/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None, None

    data = response.json()
    token = data.get("access_token")

    if not token:
        print(f"❌ No access token in response")
        print(f"Response: {json.dumps(data, indent=2)}")
        return None, None

    # Decode JWT to get user_id from 'sub' claim
    try:
        payload_b64 = token.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        user_id = payload.get('sub')

        if not user_id:
            print(f"❌ No 'sub' claim in JWT token")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return None, None
    except Exception as e:
        print(f"❌ Failed to decode JWT token: {e}")
        return None, None

    print(f"✅ Logged in, token: {token[:20]}...")
    print(f"✅ User ID: {user_id}")

    return token, user_id

def create_diagram(token, user_id, title, file_type="canvas"):
    """Create a diagram with the given title."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    # Prepare diagram data based on type
    if file_type == "canvas":
        data = {
            "title": title,
            "canvas_data": {
                "nodes": [{"id": "1", "type": "rect", "x": 0, "y": 0}],
                "edges": []
            }
        }
    elif file_type == "note":
        data = {
            "title": title,
            "note_content": f"This is a note about {title}"
        }
    else:  # mixed
        data = {
            "title": title,
            "canvas_data": {
                "nodes": [{"id": "1", "type": "rect", "x": 0, "y": 0}],
                "edges": []
            },
            "note_content": f"This is a note about {title}"
        }

    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        json=data
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram '{title}': {response.status_code}")
        print(f"Response: {response.text}")
        return None

    diagram_data = response.json()
    diagram_id = diagram_data.get("id")
    print(f"✅ Created diagram: '{title}' (ID: {diagram_id})")
    return diagram_id

def search_diagrams(token, user_id, search_query=None):
    """Search diagrams with optional search query."""
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }

    params = {}
    if search_query:
        params["search"] = search_query

    response = requests.get(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        params=params
    )

    if response.status_code != 200:
        print(f"❌ Failed to list diagrams: {response.status_code}")
        print(f"Response: {response.text}")
        return None

    data = response.json()
    diagrams = data.get("diagrams", [])
    total = data.get("total", 0)

    return diagrams, total

def validate_feature121():
    """Validate Feature #121: List diagrams with search by title."""
    print("\n" + "="*60)
    print("Feature #121 Validation: List diagrams with search by title")
    print("="*60)

    # Step 1: Register and login
    token, user_id = register_and_login()
    if not token:
        print("\n❌ VALIDATION FAILED: Could not authenticate")
        return False

    # Step 2: Create test diagrams
    print_step(2, "Create test diagrams with specific titles")

    diagram_titles = [
        "AWS Architecture",
        "Azure Architecture",
        "Database Schema"
    ]

    created_diagrams = {}
    for title in diagram_titles:
        diagram_id = create_diagram(token, user_id, title)
        if not diagram_id:
            print(f"\n❌ VALIDATION FAILED: Could not create diagram '{title}'")
            return False
        created_diagrams[title] = diagram_id

    print(f"\n✅ Created {len(created_diagrams)} diagrams")

    # Step 3: List all diagrams (no search)
    print_step(3, "List all diagrams (no search)")

    diagrams, total = search_diagrams(token, user_id)
    if diagrams is None:
        print("\n❌ VALIDATION FAILED: Could not list diagrams")
        return False

    print(f"✅ Found {total} total diagrams")
    if total < 3:
        print(f"❌ VALIDATION FAILED: Expected at least 3 diagrams, got {total}")
        return False

    # Verify all 3 created diagrams are present
    diagram_titles_found = [d.get("title") for d in diagrams]
    for title in diagram_titles:
        if title not in diagram_titles_found:
            print(f"❌ VALIDATION FAILED: Diagram '{title}' not found in list")
            return False

    print(f"✅ All 3 created diagrams found in list")

    # Step 4: Search for "Architecture"
    print_step(4, "Search for 'Architecture'")

    diagrams, total = search_diagrams(token, user_id, "Architecture")
    if diagrams is None:
        print("\n❌ VALIDATION FAILED: Could not search diagrams")
        return False

    print(f"✅ Search returned {total} diagrams")

    # Verify exactly 2 diagrams (AWS and Azure)
    if total < 2:
        print(f"❌ VALIDATION FAILED: Expected at least 2 diagrams with 'Architecture', got {total}")
        return False

    diagram_titles_found = [d.get("title") for d in diagrams]
    expected_titles = ["AWS Architecture", "Azure Architecture"]

    for title in expected_titles:
        if title not in diagram_titles_found:
            print(f"❌ VALIDATION FAILED: Expected '{title}' in search results")
            return False

    # Verify "Database Schema" is NOT in results
    if "Database Schema" in diagram_titles_found:
        print(f"❌ VALIDATION FAILED: 'Database Schema' should not be in 'Architecture' search results")
        return False

    print(f"✅ Search correctly returned AWS Architecture and Azure Architecture")
    print(f"✅ Database Schema correctly excluded")

    # Step 5: Search for "AWS"
    print_step(5, "Search for 'AWS'")

    diagrams, total = search_diagrams(token, user_id, "AWS")
    if diagrams is None:
        print("\n❌ VALIDATION FAILED: Could not search diagrams")
        return False

    print(f"✅ Search returned {total} diagrams")

    # Verify exactly 1 diagram (AWS Architecture)
    if total < 1:
        print(f"❌ VALIDATION FAILED: Expected at least 1 diagram with 'AWS', got {total}")
        return False

    diagram_titles_found = [d.get("title") for d in diagrams]

    if "AWS Architecture" not in diagram_titles_found:
        print(f"❌ VALIDATION FAILED: Expected 'AWS Architecture' in search results")
        return False

    # Verify Azure and Database are NOT in results
    if "Azure Architecture" in diagram_titles_found:
        print(f"❌ VALIDATION FAILED: 'Azure Architecture' should not be in 'AWS' search results")
        return False

    if "Database Schema" in diagram_titles_found:
        print(f"❌ VALIDATION FAILED: 'Database Schema' should not be in 'AWS' search results")
        return False

    print(f"✅ Search correctly returned only AWS Architecture")

    # Step 6: Search is case-insensitive
    print_step(6, "Verify search is case-insensitive")

    # Search for lowercase "aws"
    diagrams_lower, total_lower = search_diagrams(token, user_id, "aws")
    if diagrams_lower is None:
        print("\n❌ VALIDATION FAILED: Could not search diagrams")
        return False

    print(f"✅ Search 'aws' (lowercase) returned {total_lower} diagrams")

    if total_lower < 1:
        print(f"❌ VALIDATION FAILED: Case-insensitive search failed")
        return False

    # Search for uppercase "ARCHITECTURE"
    diagrams_upper, total_upper = search_diagrams(token, user_id, "ARCHITECTURE")
    if diagrams_upper is None:
        print("\n❌ VALIDATION FAILED: Could not search diagrams")
        return False

    print(f"✅ Search 'ARCHITECTURE' (uppercase) returned {total_upper} diagrams")

    if total_upper < 2:
        print(f"❌ VALIDATION FAILED: Case-insensitive search failed")
        return False

    print(f"✅ Search is case-insensitive")

    # Step 7: Search for "Database"
    print_step(7, "Search for 'Database'")

    diagrams, total = search_diagrams(token, user_id, "Database")
    if diagrams is None:
        print("\n❌ VALIDATION FAILED: Could not search diagrams")
        return False

    print(f"✅ Search returned {total} diagrams")

    if total < 1:
        print(f"❌ VALIDATION FAILED: Expected at least 1 diagram with 'Database', got {total}")
        return False

    diagram_titles_found = [d.get("title") for d in diagrams]

    if "Database Schema" not in diagram_titles_found:
        print(f"❌ VALIDATION FAILED: Expected 'Database Schema' in search results")
        return False

    print(f"✅ Search correctly returned Database Schema")

    # Step 8: Clear search (list all again)
    print_step(8, "Clear search and verify all diagrams returned")

    diagrams, total = search_diagrams(token, user_id)
    if diagrams is None:
        print("\n❌ VALIDATION FAILED: Could not list diagrams")
        return False

    print(f"✅ Found {total} total diagrams")

    if total < 3:
        print(f"❌ VALIDATION FAILED: Expected at least 3 diagrams after clearing search, got {total}")
        return False

    diagram_titles_found = [d.get("title") for d in diagrams]
    for title in diagram_titles:
        if title not in diagram_titles_found:
            print(f"❌ VALIDATION FAILED: Diagram '{title}' not found after clearing search")
            return False

    print(f"✅ All 3 diagrams returned after clearing search")

    # Success
    print("\n" + "="*60)
    print("TEST VALIDATION:")
    print("="*60)
    print("✅ Step 1: Registered user and logged in")
    print("✅ Step 2: Created 3 diagrams with specific titles")
    print("✅ Step 3: Listed all diagrams (verified 3+)")
    print("✅ Step 4: Searched 'Architecture' - returned AWS & Azure (not Database)")
    print("✅ Step 5: Searched 'AWS' - returned only AWS Architecture")
    print("✅ Step 6: Verified case-insensitive search")
    print("✅ Step 7: Searched 'Database' - returned Database Schema")
    print("✅ Step 8: Cleared search - all 3 diagrams returned")
    print("\n✅ Feature #121 validation PASSED")

    return True

if __name__ == "__main__":
    try:
        success = validate_feature121()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

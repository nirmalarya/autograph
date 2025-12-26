#!/usr/bin/env python3
"""
E2E Test for Feature #576: Organization: Filtering: by tags
Tests the tag filtering functionality in the diagram listing.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://localhost:8080"

def test_tag_filtering():
    """Test filtering diagrams by tags."""
    print("=" * 80)
    print("Feature #576: Organization: Filtering: by tags")
    print("=" * 80)

    # Step 1: Register and login
    print("\n1. Setting up test user...")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"tagtest{timestamp}@example.com"
    password = "SecurePass123!"

    register_response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Tag Test User"
        }
    )

    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(register_response.text)
        return False

    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    token = login_response.json()["access_token"]
    user_id = login_response.json()["user"]["id"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    print(f"✅ User created and logged in: {email}")

    # Step 2: Create diagrams with different tags
    print("\n2. Creating diagrams with tags...")

    diagrams = [
        {"name": "AWS Architecture", "tags": ["aws", "cloud", "architecture"]},
        {"name": "Azure Setup", "tags": ["azure", "cloud", "deployment"]},
        {"name": "Database Design", "tags": ["database", "sql", "design"]},
        {"name": "Cloud Network", "tags": ["aws", "network", "vpc"]},
        {"name": "No Tags Diagram", "tags": []},
    ]

    created_diagrams = []
    for diagram_data in diagrams:
        response = requests.post(
            f"{BASE_URL}/diagrams",
            headers=headers,
            json={
                "name": diagram_data["name"],
                "file_type": "canvas",
                "content": {"elements": [], "version": "1.0"},
                "tags": diagram_data["tags"]
            }
        )

        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create diagram '{diagram_data['name']}': {response.status_code}")
            return False

        created_diagrams.append(response.json())
        print(f"✅ Created: {diagram_data['name']} with tags {diagram_data['tags']}")

    # Step 3: Test filtering by single tag
    print("\n3. Testing filter by single tag...")

    test_cases = [
        ("aws", ["AWS Architecture", "Cloud Network"]),
        ("cloud", ["AWS Architecture", "Azure Setup"]),
        ("database", ["Database Design"]),
        ("azure", ["Azure Setup"]),
        ("nonexistent", []),
    ]

    for tag, expected_names in test_cases:
        # Use the search parameter with tag: prefix
        response = requests.get(
            f"{BASE_URL}/diagrams",
            headers=headers,
            params={"search": f"tag:{tag}"}
        )

        if response.status_code != 200:
            print(f"❌ Failed to filter by tag '{tag}': {response.status_code}")
            return False

        results = response.json()
        found_names = [d["name"] for d in results.get("diagrams", [])]

        # Check if all expected diagrams are found
        missing = [name for name in expected_names if name not in found_names]
        unexpected = [name for name in found_names if name not in expected_names and name in [d["name"] for d in diagrams]]

        if missing or unexpected:
            print(f"❌ Tag filter '{tag}' returned wrong results:")
            print(f"   Expected: {expected_names}")
            print(f"   Found: {found_names}")
            if missing:
                print(f"   Missing: {missing}")
            if unexpected:
                print(f"   Unexpected: {unexpected}")
            return False

        print(f"✅ Tag '{tag}' filter correct: found {len(found_names)} diagram(s)")

    # Step 4: Test combined search with tag filter
    print("\n4. Testing combined search with tag filter...")

    response = requests.get(
        f"{BASE_URL}/diagrams",
        headers=headers,
        params={"search": "Architecture tag:aws"}
    )

    if response.status_code != 200:
        print(f"❌ Combined search failed: {response.status_code}")
        return False

    results = response.json()
    found_names = [d["name"] for d in results.get("diagrams", [])]

    # Should find "AWS Architecture" (has both "Architecture" in name and "aws" tag)
    if "AWS Architecture" not in found_names:
        print(f"❌ Combined search didn't find 'AWS Architecture': {found_names}")
        return False

    # Should NOT find "Cloud Network" (has "aws" tag but not "Architecture" in name)
    if "Cloud Network" in found_names:
        print(f"❌ Combined search incorrectly included 'Cloud Network': {found_names}")
        return False

    print(f"✅ Combined search with tag filter works correctly")

    # Step 5: Test case-insensitive tag filtering
    print("\n5. Testing case-insensitive tag filtering...")

    response = requests.get(
        f"{BASE_URL}/diagrams",
        headers=headers,
        params={"search": "tag:AWS"}  # Uppercase
    )

    if response.status_code != 200:
        print(f"❌ Case-insensitive filter failed: {response.status_code}")
        return False

    results = response.json()
    found_names = [d["name"] for d in results.get("diagrams", [])]

    # Should find diagrams with "aws" tag (case-insensitive)
    if "AWS Architecture" not in found_names or "Cloud Network" not in found_names:
        print(f"❌ Case-insensitive tag filter failed: {found_names}")
        return False

    print(f"✅ Case-insensitive tag filtering works")

    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #576 is fully functional!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_tag_filtering()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

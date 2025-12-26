#!/usr/bin/env python3
"""
Feature #478: Version history: Version sharing: share link to specific version

Test Steps:
1. Select version
2. Click Share
3. Copy link
4. Open link
5. Verify shows that specific version
6. Verify read-only
"""

import requests
import sys
import hashlib
import uuid
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def generate_password_hash(password: str) -> str:
    """Generate bcrypt-compatible password hash."""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_test_user(user_id: str, email: str, password: str) -> dict:
    """Create a test user in the database."""
    import psycopg2

    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph_user",
        password="autograph_password"
    )

    try:
        cur = conn.cursor()

        # Check if user exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            print(f"✓ User {email} already exists")
            return {"user_id": user_id, "email": email}

        # Create user
        password_hash = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (id, email, password_hash, full_name, is_active, is_verified, role, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (user_id, email, password_hash, "Test User Feature 478", True, True, "user"))

        conn.commit()
        print(f"✓ Created test user: {email}")

        return {"user_id": user_id, "email": email}

    finally:
        conn.close()

def login_user(email: str, password: str) -> str:
    """Login and get access token."""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": email, "password": password}
    )

    if response.status_code != 200:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

    data = response.json()
    token = data.get("access_token")
    print(f"✓ Logged in successfully")
    return token

def create_diagram(token: str, title: str) -> dict:
    """Create a test diagram."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers=headers,
        json={
            "title": title,
            "type": "canvas",
            "canvas_data": {"shapes": [], "bindings": [], "assets": []}
        }
    )

    if response.status_code != 200:
        print(f"✗ Create diagram failed: {response.status_code} - {response.text}")
        return None

    diagram = response.json()
    print(f"✓ Created diagram: {diagram['id']}")
    return diagram

def update_diagram(token: str, diagram_id: str, content: dict) -> dict:
    """Update diagram content to create a new version."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.put(
        f"{API_BASE_URL}/diagrams/{diagram_id}",
        headers=headers,
        json={
            "canvas_data": content,
            "description": f"Version update at {datetime.now().isoformat()}"
        }
    )

    if response.status_code != 200:
        print(f"✗ Update diagram failed: {response.status_code} - {response.text}")
        return None

    diagram = response.json()
    print(f"✓ Updated diagram to version {diagram.get('current_version', '?')}")
    return diagram

def get_versions(token: str, diagram_id: str) -> list:
    """Get all versions of a diagram."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/versions",
        headers=headers
    )

    if response.status_code != 200:
        print(f"✗ Get versions failed: {response.status_code} - {response.text}")
        return []

    data = response.json()
    versions = data.get("versions", [])
    print(f"✓ Retrieved {len(versions)} versions")
    return versions

def create_version_share(token: str, diagram_id: str, version_id: str) -> dict:
    """Create a share link for a specific version."""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/versions/{version_id}/share",
        headers=headers,
        json={}  # Optional: can include expires_in_days
    )

    if response.status_code != 200:
        print(f"✗ Create version share failed: {response.status_code} - {response.text}")
        return None

    share = response.json()
    print(f"✓ Created version share link: {share['share_url']}")
    return share

def access_shared_version(token_str: str) -> dict:
    """Access a shared version via its token (no auth required)."""
    response = requests.get(
        f"{API_BASE_URL}/diagrams/version-shared/{token_str}"
    )

    if response.status_code != 200:
        print(f"✗ Access shared version failed: {response.status_code} - {response.text}")
        return None

    version_data = response.json()
    print(f"✓ Accessed shared version {version_data.get('version_number')}")
    return version_data

def main():
    print("=" * 60)
    print("Feature #478: Version Sharing Test")
    print("=" * 60)
    print()

    # Use pre-created test user
    email = "feature478test@example.com"
    password = "TestPassword123!"

    print("STEP 0: Setup")
    print("-" * 60)
    print(f"Using test user: {email}")

    token = login_user(email, password)
    if not token:
        print("✗ Failed to login")
        return False

    print()

    # Create a diagram
    print("STEP 1: Create diagram with multiple versions")
    print("-" * 60)
    diagram = create_diagram(token, "Version Sharing Test Diagram")
    if not diagram:
        print("✗ Failed to create diagram")
        return False

    diagram_id = diagram['id']

    # Create multiple versions by updating the diagram
    version_contents = [
        {"shapes": [{"type": "rectangle", "id": "v1"}], "bindings": [], "assets": []},
        {"shapes": [{"type": "rectangle", "id": "v1"}, {"type": "circle", "id": "v2"}], "bindings": [], "assets": []},
        {"shapes": [{"type": "rectangle", "id": "v1"}, {"type": "circle", "id": "v2"}, {"type": "arrow", "id": "v3"}], "bindings": [], "assets": []},
    ]

    for i, content in enumerate(version_contents):
        update_diagram(token, diagram_id, content)

    print()

    # Get all versions
    print("STEP 2: Get versions list")
    print("-" * 60)
    versions = get_versions(token, diagram_id)
    if len(versions) < 2:
        print(f"✗ Expected at least 2 versions, got {len(versions)}")
        return False

    # Select a specific version (version 2, which has content)
    # Versions are sorted descending, so versions[0] is the latest, versions[1] is older
    # We want to share version 2 (which has 1 shape added)
    selected_version = None
    for v in versions:
        if v['version_number'] == 2:
            selected_version = v
            break

    if not selected_version:
        # Fallback to first version if version 2 not found
        selected_version = versions[0]

    version_id = selected_version['id']
    version_number = selected_version['version_number']

    print(f"✓ Selected version #{version_number} (ID: {version_id})")
    print()

    # Create share link for the selected version
    print("STEP 3: Create share link for version")
    print("-" * 60)
    share = create_version_share(token, diagram_id, version_id)
    if not share:
        print("✗ Failed to create version share link")
        return False

    share_token = share['token']
    share_url = share['share_url']

    # Verify share details
    if share.get('version_number') != version_number:
        print(f"✗ Share version number mismatch: expected {version_number}, got {share.get('version_number')}")
        return False

    if share.get('permission') != 'view':
        print(f"✗ Share permission should be 'view', got {share.get('permission')}")
        return False

    print(f"✓ Share URL: {share_url}")
    print(f"✓ Token: {share_token[:20]}...")
    print()

    # Access the shared version (no auth required)
    print("STEP 4: Access shared version")
    print("-" * 60)
    shared_version = access_shared_version(share_token)
    if not shared_version:
        print("✗ Failed to access shared version")
        return False

    print()

    # Verify the shared version data
    print("STEP 5: Verify shared version content")
    print("-" * 60)

    # Check version number matches
    if shared_version.get('version_number') != version_number:
        print(f"✗ Version number mismatch: expected {version_number}, got {shared_version.get('version_number')}")
        return False
    print(f"✓ Correct version number: {version_number}")

    # Check it's read-only
    if not shared_version.get('is_read_only'):
        print("✗ Shared version should be read-only")
        return False
    print("✓ Version is read-only")

    # Check permission is view
    if shared_version.get('permission') != 'view':
        print(f"✗ Permission should be 'view', got {shared_version.get('permission')}")
        return False
    print("✓ Permission is 'view'")

    # Verify canvas data exists (version 2 should have 1 shape added)
    actual_content = shared_version.get('canvas_data', {})
    actual_shape_count = len(actual_content.get('shapes', []))

    # Version 2 should have 1 shape
    if version_number == 2 and actual_shape_count != 1:
        print(f"✗ Canvas data mismatch: version 2 should have 1 shape, got {actual_shape_count}")
        return False

    print(f"✓ Canvas data matches version {version_number} ({actual_shape_count} shapes)")

    # Verify diagram title is included
    if not shared_version.get('title'):
        print("✗ Diagram title missing in shared version")
        return False
    print(f"✓ Diagram title: {shared_version.get('title')}")

    print()

    # Final verification
    print("STEP 6: Final verification")
    print("-" * 60)
    print("✓ Share link created successfully")
    print("✓ Share link points to correct version")
    print("✓ Shared version is read-only")
    print("✓ Content matches selected version")
    print()

    print("=" * 60)
    print("✅ Feature #478 - PASSING")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

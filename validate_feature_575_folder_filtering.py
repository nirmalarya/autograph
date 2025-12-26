#!/usr/bin/env python3
"""
Feature #575: Organization: Filtering: by folder
Test that diagrams can be filtered by folder.
"""

import requests
import json
import sys
import uuid
from datetime import datetime

# API Configuration
API_BASE = "https://localhost:8080"
DIAGRAM_SERVICE = "https://localhost:8082"

def generate_password_hash(password: str) -> str:
    """Generate bcrypt hash for password."""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_test_user_and_login():
    """Create a test user and get auth token."""
    # Create user directly in database
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cursor = conn.cursor()

    # Create test user
    test_email = f"test_folder_575_{datetime.now().timestamp()}@example.com"
    test_password = "TestPass123!"
    password_hash = generate_password_hash(test_password)
    user_id = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO users (id, email, password_hash, full_name, plan, is_active, is_verified, role) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
        (user_id, test_email, password_hash, "Test User 575", "pro", True, True, "user")
    )
    user_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()

    # Login to get token
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": test_email, "password": test_password},
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return None, None

    data = response.json()
    return data["access_token"], user_id

def create_folder(token: str, folder_name: str, parent_id: str = None) -> str:
    """Create a folder and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": folder_name,
        "color": "#3b82f6",
        "icon": "folder"
    }
    if parent_id:
        payload["parent_id"] = parent_id

    response = requests.post(
        f"{API_BASE}/api/diagrams/folders",
        headers=headers,
        json=payload,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to create folder '{folder_name}': {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    return data["id"]

def create_diagram(token: str, title: str, folder_id: str = None) -> str:
    """Create a diagram and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "title": title,
        "file_type": "canvas",
        "canvas_data": {"shapes": [], "connections": []}
    }
    if folder_id:
        payload["folder_id"] = folder_id

    response = requests.post(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        json=payload,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to create diagram '{title}': {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    return data["id"]

def list_diagrams_by_folder(token: str, folder_id: str = None) -> list:
    """List diagrams filtered by folder."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {}
    if folder_id is not None:
        params["folder_id"] = folder_id

    response = requests.get(
        f"{API_BASE}/api/diagrams",
        headers=headers,
        params=params,
        verify=False
    )

    if response.status_code != 200:
        print(f"❌ Failed to list diagrams: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    return data.get("diagrams", [])

def main():
    """Test folder filtering functionality."""
    print("=" * 80)
    print("Feature #575: Organization: Filtering: by folder")
    print("=" * 80)

    # Step 1: Create test user and login
    print("\n1. Creating test user and logging in...")
    token, user_id = create_test_user_and_login()
    if not token:
        print("❌ FAILED: Could not create user or login")
        return 1
    print(f"✅ Logged in as user {user_id}")

    # Step 2: Create folders
    print("\n2. Creating test folders...")
    architecture_folder_id = create_folder(token, "Architecture")
    if not architecture_folder_id:
        print("❌ FAILED: Could not create Architecture folder")
        return 1
    print(f"✅ Created folder 'Architecture': {architecture_folder_id}")

    design_folder_id = create_folder(token, "Design")
    if not design_folder_id:
        print("❌ FAILED: Could not create Design folder")
        return 1
    print(f"✅ Created folder 'Design': {design_folder_id}")

    # Step 3: Create diagrams in different folders
    print("\n3. Creating test diagrams...")

    # Create 2 diagrams in Architecture folder
    arch_diagram_1 = create_diagram(token, "AWS Architecture", architecture_folder_id)
    arch_diagram_2 = create_diagram(token, "System Design", architecture_folder_id)

    # Create 2 diagrams in Design folder
    design_diagram_1 = create_diagram(token, "UI Mockup", design_folder_id)
    design_diagram_2 = create_diagram(token, "User Flow", design_folder_id)

    # Create 1 diagram in root (no folder)
    root_diagram = create_diagram(token, "Untitled Diagram", None)

    if not all([arch_diagram_1, arch_diagram_2, design_diagram_1, design_diagram_2, root_diagram]):
        print("❌ FAILED: Could not create all diagrams")
        return 1

    print(f"✅ Created 5 diagrams across folders")

    # Step 4: Test filtering by Architecture folder
    print("\n4. Testing filter: Folder = Architecture...")
    architecture_diagrams = list_diagrams_by_folder(token, architecture_folder_id)
    if architecture_diagrams is None:
        print("❌ FAILED: Could not list diagrams")
        return 1

    print(f"   Found {len(architecture_diagrams)} diagrams")

    # Verify only Architecture folder diagrams are returned
    architecture_titles = [d["title"] for d in architecture_diagrams]
    print(f"   Diagrams: {architecture_titles}")

    if len(architecture_diagrams) != 2:
        print(f"❌ FAILED: Expected 2 diagrams in Architecture folder, got {len(architecture_diagrams)}")
        return 1

    if not all(d["folder_id"] == architecture_folder_id for d in architecture_diagrams):
        print("❌ FAILED: Some diagrams are not in Architecture folder")
        return 1

    print("✅ Only diagrams in Architecture folder returned")

    # Step 5: Test filtering by Design folder
    print("\n5. Testing filter: Folder = Design...")
    design_diagrams = list_diagrams_by_folder(token, design_folder_id)
    if design_diagrams is None:
        print("❌ FAILED: Could not list diagrams")
        return 1

    print(f"   Found {len(design_diagrams)} diagrams")

    if len(design_diagrams) != 2:
        print(f"❌ FAILED: Expected 2 diagrams in Design folder, got {len(design_diagrams)}")
        return 1

    if not all(d["folder_id"] == design_folder_id for d in design_diagrams):
        print("❌ FAILED: Some diagrams are not in Design folder")
        return 1

    print("✅ Only diagrams in Design folder returned")

    # Step 6: Test listing all diagrams (no filter)
    print("\n6. Testing no filter (all diagrams)...")
    all_diagrams = list_diagrams_by_folder(token, None)
    if all_diagrams is None:
        print("❌ FAILED: Could not list diagrams")
        return 1

    print(f"   Found {len(all_diagrams)} diagrams")

    if len(all_diagrams) != 5:
        print(f"❌ FAILED: Expected 5 total diagrams, got {len(all_diagrams)}")
        return 1

    print("✅ All diagrams returned when no filter applied")

    # Success!
    print("\n" + "=" * 80)
    print("✅ Feature #575 PASSED: Folder filtering works correctly")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

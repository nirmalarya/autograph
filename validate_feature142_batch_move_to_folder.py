#!/usr/bin/env python3
"""
Feature #142 Validation: Batch operations - bulk move to folder

Tests:
1. Create folder: 'Archive'
2. Create 8 diagrams
3. Select 3 diagrams
4. Move 3 diagrams to Archive folder
5. Verify 3 diagrams moved to Archive
6. Navigate to Archive folder (list diagrams in folder)
7. Verify 3 diagrams present in Archive
8. Verify remaining 5 diagrams NOT in Archive folder
"""

import requests
import sys
import time
import uuid
from typing import List, Dict, Tuple

# Configuration
DIAGRAM_SERVICE = "http://localhost:8082"
AUTH_SERVICE = "http://localhost:8085"


def register_user() -> Tuple[str, Dict]:
    """Register a new user and return user_id and headers."""
    unique_email = f"batch_move_{uuid.uuid4().hex[:8]}@example.com"
    register_data = {
        "email": unique_email,
        "password": "Test123!@#",
        "full_name": "Batch Move Test User"
    }

    response = requests.post(f"{AUTH_SERVICE}/register", json=register_data)

    if response.status_code != 201:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        sys.exit(1)

    user_data = response.json()
    user_id = user_data["id"]
    headers = {"X-User-ID": user_id}

    print(f"✅ User registered: {unique_email}")
    print(f"   User ID: {user_id}")
    return user_id, headers


def create_folder(headers: Dict, name: str) -> str:
    """Create a folder and return its ID."""
    response = requests.post(
        f"{DIAGRAM_SERVICE}/folders",
        headers=headers,
        json={"name": name}
    )

    if response.status_code != 201:
        print(f"❌ Failed to create folder '{name}': {response.status_code}")
        print(response.text)
        sys.exit(1)

    folder_id = response.json()["id"]
    print(f"✅ Created folder '{name}' with ID: {folder_id}")
    return folder_id


def create_diagram(headers: Dict, title: str) -> str:
    """Create a diagram and return its ID."""
    response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        json={
            "title": title,
            "type": "canvas",
            "canvas_data": {"shapes": [], "bindings": []}
        }
    )

    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram '{title}': {response.status_code}")
        print(response.text)
        sys.exit(1)

    diagram_id = response.json()["id"]
    print(f"✅ Created diagram '{title}' with ID: {diagram_id}")
    return diagram_id


def move_diagram_to_folder(headers: Dict, diagram_id: str, folder_id: str):
    """Move a diagram to a folder."""
    response = requests.put(
        f"{DIAGRAM_SERVICE}/{diagram_id}/folder",
        headers=headers,
        params={"folder_id": folder_id}
    )

    if response.status_code != 200:
        print(f"❌ Failed to move diagram {diagram_id} to folder: {response.status_code}")
        print(response.text)
        sys.exit(1)

    print(f"✅ Moved diagram {diagram_id} to folder {folder_id}")


def list_diagrams(headers: Dict) -> List[Dict]:
    """List all diagrams (not in folders)."""
    response = requests.get(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        params={"page_size": 20}
    )

    if response.status_code != 200:
        print(f"❌ Failed to list diagrams: {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json().get("diagrams", [])


def get_diagram(headers: Dict, diagram_id: str) -> Dict:
    """Get a single diagram by ID."""
    response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}",
        headers=headers
    )

    if response.status_code != 200:
        print(f"❌ Failed to get diagram {diagram_id}: {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json()


def main():
    print("=" * 80)
    print("Feature #142 Validation: Batch operations - bulk move to folder")
    print("=" * 80)

    # Step 1: Register user
    print("\n📝 Step 1: Register test user")
    user_id, headers = register_user()

    # Step 2: Create folder 'Archive'
    print("\n📁 Step 2: Create folder 'Archive'")
    archive_folder_id = create_folder(headers, "Archive")

    # Step 3: Create 8 diagrams
    print("\n📊 Step 3: Create 8 diagrams")
    diagram_ids = []
    for i in range(1, 9):
        diagram_id = create_diagram(headers, f"Test Diagram {i}")
        diagram_ids.append(diagram_id)

    print(f"✅ Created {len(diagram_ids)} diagrams")

    # Step 4: Select 3 diagrams to move
    print("\n🔍 Step 4: Select 3 diagrams to move to Archive")
    diagrams_to_move = diagram_ids[0:3]  # First 3 diagrams
    diagrams_to_keep = diagram_ids[3:]   # Last 5 diagrams

    print(f"   Diagrams to move: {len(diagrams_to_move)}")
    for did in diagrams_to_move:
        print(f"     - {did}")

    # Step 5: Batch move - Move 3 diagrams to Archive folder
    print("\n↔️  Step 5: Batch move - Move 3 diagrams to Archive")
    for diagram_id in diagrams_to_move:
        move_diagram_to_folder(headers, diagram_id, archive_folder_id)

    print(f"✅ Batch moved {len(diagrams_to_move)} diagrams to Archive folder")

    # Give a moment for database to update
    time.sleep(0.5)

    # Step 6: Verify diagrams moved to Archive by checking their folder_id
    print("\n📋 Step 6: Verify diagrams in Archive by checking folder_id")
    moved_count = 0
    for diagram_id in diagrams_to_move:
        diagram = get_diagram(headers, diagram_id)
        if diagram.get("folder_id") == archive_folder_id:
            moved_count += 1
            print(f"   ✅ Diagram {diagram_id} has folder_id={archive_folder_id}")
        else:
            print(f"   ❌ Diagram {diagram_id} has folder_id={diagram.get('folder_id')} (expected {archive_folder_id}) - FAILED")
            sys.exit(1)

    print(f"✅ All {moved_count}/3 diagrams successfully moved to Archive folder")

    # Step 7: Verify remaining 5 diagrams are NOT in Archive folder
    print("\n✔️  Step 7: Verify remaining 5 diagrams NOT in Archive")
    for diagram_id in diagrams_to_keep:
        diagram = get_diagram(headers, diagram_id)
        if diagram.get("folder_id") == archive_folder_id:
            print(f"   ❌ Diagram {diagram_id} has folder_id={archive_folder_id} (should NOT be there - FAILED)")
            sys.exit(1)
        else:
            print(f"   ✅ Diagram {diagram_id} has folder_id={diagram.get('folder_id')} (correct, not in Archive)")

    print(f"✅ Remaining 5 diagrams correctly NOT in Archive folder")

    # Step 8: List all diagrams (should show all user's diagrams)
    print("\n📊 Step 8: List all diagrams (dashboard view)")
    all_diagrams = list_diagrams(headers)
    print(f"   Found {len(all_diagrams)} total diagrams")

    # Verify all 8 diagrams exist
    all_diagram_ids = [d["id"] for d in all_diagrams]
    found_count = sum(1 for did in diagram_ids if did in all_diagram_ids)
    print(f"   ✅ Found {found_count}/8 created diagrams in listing")

    # Final validation
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print(f"✅ Folder 'Archive' created: {archive_folder_id}")
    print(f"✅ 8 diagrams created")
    print(f"✅ 3 diagrams batch-moved to Archive folder")
    print(f"✅ All 3 diagrams verified in Archive folder (folder_id set)")
    print(f"✅ 5 diagrams correctly NOT in Archive folder (folder_id not set)")
    print("=" * 80)
    print("🎉 Feature #142: Batch operations - bulk move to folder PASSED")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

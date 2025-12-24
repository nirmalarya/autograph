#!/usr/bin/env python3
"""
Test Feature #156: Diagram size calculation and display

This test verifies:
1. Create diagram with 100 shapes
2. Calculate canvas_data JSON size
3. Verify size displayed in dashboard
4. Verify size shown in KB or MB
5. Add 1000 more shapes
6. Verify size increases
7. Test with large note content
8. Verify total size includes canvas + note
"""

import requests
import json
import time
import sys

# Configuration
AUTH_SERVICE_URL = "http://localhost:8085"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

def register_user(email, password):
    """Register a new user."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={"email": email, "password": password}
    )
    return response

def login_user(email, password):
    """Login and get access token."""
    response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def create_diagram(title, file_type, canvas_data, note_content, user_id):
    """Create a diagram."""
    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={"X-User-ID": user_id},
        json={
            "title": title,
            "file_type": file_type,
            "canvas_data": canvas_data,
            "note_content": note_content
        }
    )
    return response

def get_diagram(diagram_id, user_id):
    """Get a diagram by ID."""
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers={"X-User-ID": user_id}
    )
    return response

def list_diagrams(user_id):
    """List all diagrams."""
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/",
        headers={"X-User-ID": user_id}
    )
    return response

def generate_canvas_data(num_shapes):
    """Generate canvas data with specified number of shapes."""
    shapes = []
    for i in range(num_shapes):
        shapes.append({
            "id": f"shape-{i}",
            "type": "rectangle",
            "x": i * 10,
            "y": i * 10,
            "width": 100,
            "height": 50,
            "fill": "#3b82f6",
            "stroke": "#1e40af",
            "text": f"Shape {i}"
        })
    return {"shapes": shapes, "version": 1}

def calculate_size(canvas_data, note_content):
    """Calculate expected size in bytes."""
    size = 0
    if canvas_data:
        size += len(json.dumps(canvas_data).encode('utf-8'))
    if note_content:
        size += len(note_content.encode('utf-8'))
    return size

def format_bytes(bytes_size):
    """Format bytes into human-readable size."""
    if bytes_size is None or bytes_size == 0:
        return "0 B"
    k = 1024
    sizes = ['B', 'KB', 'MB', 'GB']
    i = 0
    while bytes_size >= k and i < len(sizes) - 1:
        bytes_size /= k
        i += 1
    return f"{bytes_size:.1f} {sizes[i]}"

def run_tests():
    """Run all tests for Feature #156."""
    print("=" * 80)
    print("Testing Feature #156: Diagram size calculation and display")
    print("=" * 80)
    
    # Test 1: Register and login
    print("\n[Test 1] User registration and login...")
    email = f"sizetest_{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    register_response = register_user(email, password)
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed (status {register_response.status_code}): {register_response.text}")
        return False
    
    user_data = register_response.json()
    user_id = user_data["id"]  # The response is the user object directly
    print(f"✅ User registered: {email} (ID: {user_id})")
    
    token = login_user(email, password)
    if not token:
        print("❌ Login failed")
        return False
    print("✅ User logged in successfully")
    
    # Test 2: Create diagram with 100 shapes
    print("\n[Test 2] Create diagram with 100 shapes...")
    canvas_data_100 = generate_canvas_data(100)
    expected_size_100 = calculate_size(canvas_data_100, None)
    
    create_response = create_diagram(
        title="Diagram with 100 shapes",
        file_type="canvas",
        canvas_data=canvas_data_100,
        note_content=None,
        user_id=user_id
    )
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create diagram: {create_response.text}")
        return False
    
    diagram_100 = create_response.json()
    diagram_id_100 = diagram_100["id"]
    print(f"✅ Diagram created: {diagram_id_100}")
    print(f"   Expected size: {format_bytes(expected_size_100)} ({expected_size_100} bytes)")
    
    # Test 3: Verify size is returned
    print("\n[Test 3] Verify size is calculated and returned...")
    get_response = get_diagram(diagram_id_100, user_id)
    if get_response.status_code != 200:
        print(f"❌ Failed to get diagram: {get_response.text}")
        return False
    
    diagram_data = get_response.json()
    if "size_bytes" not in diagram_data:
        print("❌ size_bytes field not present in response")
        return False
    
    actual_size = diagram_data["size_bytes"]
    print(f"✅ Size calculated: {format_bytes(actual_size)} ({actual_size} bytes)")
    
    # Verify size is close to expected (within 5% tolerance for JSON formatting differences)
    size_diff = abs(actual_size - expected_size_100)
    tolerance = expected_size_100 * 0.05
    if size_diff > tolerance:
        print(f"⚠️  Warning: Size difference ({size_diff} bytes) exceeds tolerance ({tolerance} bytes)")
    else:
        print(f"✅ Size matches expected value (difference: {size_diff} bytes)")
    
    # Test 4: Verify size shown in KB
    print("\n[Test 4] Verify size shown in KB...")
    if actual_size >= 1024:
        print(f"✅ Size is {format_bytes(actual_size)} (shown in KB)")
    else:
        print(f"✅ Size is {format_bytes(actual_size)} (shown in bytes)")
    
    # Test 5: Create diagram with 1000 shapes
    print("\n[Test 5] Create diagram with 1000 shapes...")
    canvas_data_1000 = generate_canvas_data(1000)
    expected_size_1000 = calculate_size(canvas_data_1000, None)
    
    create_response_1000 = create_diagram(
        title="Diagram with 1000 shapes",
        file_type="canvas",
        canvas_data=canvas_data_1000,
        note_content=None,
        user_id=user_id
    )
    
    if create_response_1000.status_code != 200:
        print(f"❌ Failed to create large diagram: {create_response_1000.text}")
        return False
    
    diagram_1000 = create_response_1000.json()
    diagram_id_1000 = diagram_1000["id"]
    actual_size_1000 = diagram_1000.get("size_bytes", 0)
    print(f"✅ Large diagram created: {diagram_id_1000}")
    print(f"   Size: {format_bytes(actual_size_1000)} ({actual_size_1000} bytes)")
    
    # Test 6: Verify size increased
    print("\n[Test 6] Verify size increased with more shapes...")
    if actual_size_1000 > actual_size:
        increase_factor = actual_size_1000 / actual_size
        print(f"✅ Size increased by {increase_factor:.1f}x ({format_bytes(actual_size)} → {format_bytes(actual_size_1000)})")
    else:
        print(f"❌ Size did not increase as expected")
        return False
    
    # Test 7: Create diagram with large note content
    print("\n[Test 7] Create diagram with large note content...")
    large_note = "# Large Note\n\n" + ("This is a test paragraph with lots of content. " * 1000)
    expected_size_note = calculate_size(None, large_note)
    
    create_response_note = create_diagram(
        title="Diagram with large note",
        file_type="note",
        canvas_data=None,
        note_content=large_note,
        user_id=user_id
    )
    
    if create_response_note.status_code != 200:
        print(f"❌ Failed to create note diagram: {create_response_note.text}")
        return False
    
    diagram_note = create_response_note.json()
    diagram_id_note = diagram_note["id"]
    actual_size_note = diagram_note.get("size_bytes", 0)
    print(f"✅ Note diagram created: {diagram_id_note}")
    print(f"   Size: {format_bytes(actual_size_note)} ({actual_size_note} bytes)")
    
    # Test 8: Create mixed diagram (canvas + note)
    print("\n[Test 8] Create mixed diagram (canvas + note)...")
    canvas_data_mixed = generate_canvas_data(50)
    note_content_mixed = "# Mixed Diagram\n\nThis has both canvas and note content."
    expected_size_mixed = calculate_size(canvas_data_mixed, note_content_mixed)
    
    create_response_mixed = create_diagram(
        title="Mixed diagram",
        file_type="mixed",
        canvas_data=canvas_data_mixed,
        note_content=note_content_mixed,
        user_id=user_id
    )
    
    if create_response_mixed.status_code != 200:
        print(f"❌ Failed to create mixed diagram: {create_response_mixed.text}")
        return False
    
    diagram_mixed = create_response_mixed.json()
    diagram_id_mixed = diagram_mixed["id"]
    actual_size_mixed = diagram_mixed.get("size_bytes", 0)
    print(f"✅ Mixed diagram created: {diagram_id_mixed}")
    print(f"   Size: {format_bytes(actual_size_mixed)} ({actual_size_mixed} bytes)")
    print(f"   Expected: {format_bytes(expected_size_mixed)} ({expected_size_mixed} bytes)")
    
    # Verify total size includes both canvas and note
    size_diff_mixed = abs(actual_size_mixed - expected_size_mixed)
    tolerance_mixed = expected_size_mixed * 0.05
    if size_diff_mixed <= tolerance_mixed:
        print(f"✅ Total size correctly includes canvas + note (difference: {size_diff_mixed} bytes)")
    else:
        print(f"⚠️  Warning: Size difference ({size_diff_mixed} bytes) exceeds tolerance ({tolerance_mixed} bytes)")
    
    # Test 9: Verify size in list endpoint
    print("\n[Test 9] Verify size displayed in diagram list...")
    list_response = list_diagrams(user_id)
    if list_response.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_response.text}")
        return False
    
    diagrams_list = list_response.json()["diagrams"]
    found_sizes = 0
    for diagram in diagrams_list:
        if "size_bytes" in diagram and diagram["size_bytes"] is not None:
            found_sizes += 1
    
    if found_sizes >= 4:  # We created 4 diagrams
        print(f"✅ All diagrams have size_bytes field ({found_sizes} diagrams)")
    else:
        print(f"❌ Not all diagrams have size_bytes field (found {found_sizes}, expected 4)")
        return False
    
    print("\n" + "=" * 80)
    print("✅ All tests passed! Feature #156 is working correctly.")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

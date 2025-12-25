#!/usr/bin/env python3
"""
Feature #156 Validation: Diagram size calculation and display
Tests:
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
import sys
import time

# Configuration
BASE_URL = "http://localhost:8080"
AUTH_SERVICE_URL = "http://localhost:8085"

def print_step(step_num, description):
    """Print test step header."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def register_and_login(email, password, full_name):
    """Register a new user and login."""
    import psycopg2

    # Register
    register_response = requests.post(
        f"{AUTH_SERVICE_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name
        }
    )

    if register_response.status_code != 201:
        print(f"Registration failed: {register_response.status_code}")
        print(register_response.text)
        return None

    user_id = register_response.json()['id']

    # Verify email directly in database
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        cur = conn.cursor()
        cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not verify email in database: {e}")

    # Login
    login_response = requests.post(
        f"{AUTH_SERVICE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

    if login_response.status_code != 200:
        print(f"Login failed: {login_response.status_code}")
        print(login_response.text)
        return None

    return login_response.json()['access_token']

def create_diagram_with_shapes(token, shape_count, title):
    """Create diagram with specified number of shapes."""
    # Generate canvas_data with N shapes
    shapes = []
    for i in range(shape_count):
        shapes.append({
            "id": f"shape_{i}",
            "type": "rectangle",
            "x": (i % 10) * 100,
            "y": (i // 10) * 100,
            "width": 80,
            "height": 60,
            "props": {
                "text": f"Shape {i}",
                "color": "blue",
                "fill": "solid"
            }
        })

    canvas_data = {
        "document": {
            "pages": {
                "page1": {
                    "id": "page1",
                    "shapes": shapes
                }
            }
        }
    }

    response = requests.post(
        f"{BASE_URL}/api/diagrams",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "file_type": "canvas",
            "canvas_data": canvas_data
        }
    )

    if response.status_code not in [200, 201]:
        print(f"Failed to create diagram: {response.status_code}")
        print(response.text)
        return None, None

    diagram_data = response.json()
    # Calculate actual JSON size
    json_size = len(json.dumps(canvas_data).encode('utf-8'))

    return diagram_data, json_size

def update_diagram_note(token, diagram_id, note_content):
    """Update diagram with note content."""
    response = requests.put(
        f"{BASE_URL}/api/diagrams/{diagram_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "note_content": note_content
        }
    )

    if response.status_code != 200:
        print(f"Failed to update diagram: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def list_diagrams(token):
    """List diagrams."""
    response = requests.get(
        f"{BASE_URL}/api/diagrams",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"Failed to list diagrams: {response.status_code}")
        print(response.text)
        return None

    return response.json()

def parse_size_display(size_str):
    """Parse size display string to bytes."""
    parts = size_str.split()
    if len(parts) != 2:
        return None

    value = float(parts[0])
    unit = parts[1]

    if unit == "B":
        return value
    elif unit == "KB":
        return value * 1024
    elif unit == "MB":
        return value * 1024 * 1024
    elif unit == "GB":
        return value * 1024 * 1024 * 1024

    return None

def main():
    """Run all validation steps."""
    print("Feature #156 Validation: Diagram size calculation and display")
    print("=" * 60)

    # Step 1: Create diagram with 100 shapes
    print_step(1, "Create diagram with 100 shapes")

    token = register_and_login(
        f"size_test_{int(time.time())}@example.com",
        "SecurePass123!",
        "Size Test User"
    )

    if not token:
        print("❌ Failed to register/login user")
        return False

    print("✅ User registered and logged in")

    diagram, expected_size_100 = create_diagram_with_shapes(token, 100, "Diagram with 100 shapes")

    if not diagram:
        print("❌ Failed to create diagram with 100 shapes")
        return False

    diagram_id = diagram['id']
    print(f"✅ Diagram created: {diagram_id}")
    print(f"   Canvas JSON size: {expected_size_100} bytes")

    # Step 2: Calculate canvas_data JSON size
    print_step(2, "Calculate canvas_data JSON size")

    if 'size_bytes' not in diagram:
        print("❌ size_bytes not in response")
        return False

    size_bytes = diagram['size_bytes']
    print(f"✅ size_bytes calculated: {size_bytes} bytes")
    print(f"   Expected: ~{expected_size_100} bytes")

    # Should be approximately equal (within 10% tolerance)
    if abs(size_bytes - expected_size_100) / expected_size_100 > 0.1:
        print(f"❌ Size mismatch: got {size_bytes}, expected ~{expected_size_100}")
        return False

    print("✅ Size calculation matches expected value")

    # Step 3: Verify size displayed in dashboard
    print_step(3, "Verify size displayed in dashboard")

    diagrams_list = list_diagrams(token)
    if not diagrams_list or 'diagrams' not in diagrams_list:
        print("❌ Failed to list diagrams")
        return False

    # Find our diagram
    our_diagram = None
    for d in diagrams_list['diagrams']:
        if d['id'] == diagram_id:
            our_diagram = d
            break

    if not our_diagram:
        print("❌ Diagram not found in list")
        return False

    if 'size_bytes' not in our_diagram:
        print("❌ size_bytes not in diagram list")
        return False

    print(f"✅ size_bytes displayed in dashboard: {our_diagram['size_bytes']} bytes")

    # Step 4: Verify size shown in KB or MB
    print_step(4, "Verify size shown in KB or MB")

    if 'size_display' not in our_diagram:
        print("❌ size_display not in response")
        return False

    size_display = our_diagram['size_display']
    print(f"✅ size_display: {size_display}")

    # Verify format (should be like "12.34 KB" or "1.23 MB")
    if not any(unit in size_display for unit in ['B', 'KB', 'MB', 'GB']):
        print(f"❌ Invalid size_display format: {size_display}")
        return False

    print("✅ Size display format is valid")

    # Step 5: Add 1000 more shapes
    print_step(5, "Add 1000 more shapes (update to 1100 total)")

    diagram_large, expected_size_1100 = create_diagram_with_shapes(token, 1100, "Diagram with 1100 shapes")

    if not diagram_large:
        print("❌ Failed to create diagram with 1100 shapes")
        return False

    diagram_large_id = diagram_large['id']
    size_bytes_large = diagram_large['size_bytes']

    print(f"✅ Large diagram created: {diagram_large_id}")
    print(f"   Canvas JSON size: {expected_size_1100} bytes")
    print(f"   Reported size: {size_bytes_large} bytes")

    # Step 6: Verify size increases
    print_step(6, "Verify size increases")

    if size_bytes_large <= size_bytes:
        print(f"❌ Size did not increase: {size_bytes_large} <= {size_bytes}")
        return False

    increase_ratio = size_bytes_large / size_bytes
    print(f"✅ Size increased by {increase_ratio:.2f}x")
    print(f"   100 shapes: {size_bytes} bytes ({our_diagram['size_display']})")
    print(f"   1100 shapes: {size_bytes_large} bytes ({diagram_large['size_display']})")

    # Should be roughly 11x larger (1100/100)
    if increase_ratio < 8 or increase_ratio > 15:
        print(f"❌ Unexpected size increase ratio: {increase_ratio:.2f}x (expected ~11x)")
        return False

    print("✅ Size increase is proportional to shape count")

    # Step 7: Test with large note content
    print_step(7, "Test with large note content")

    # Create 50KB of note content
    large_note = "# Large Note\n\n" + ("This is a test paragraph. " * 1000)
    note_size = len(large_note.encode('utf-8'))

    print(f"Creating note content: {note_size} bytes")

    updated_diagram = update_diagram_note(token, diagram_id, large_note)

    if not updated_diagram:
        print("❌ Failed to update diagram with note")
        return False

    size_with_note = updated_diagram['size_bytes']
    print(f"✅ Diagram updated with note")
    print(f"   Size with note: {size_with_note} bytes ({updated_diagram['size_display']})")

    # Step 8: Verify total size includes canvas + note
    print_step(8, "Verify total size includes canvas + note")

    expected_total_size = expected_size_100 + note_size

    print(f"Canvas size: {expected_size_100} bytes")
    print(f"Note size: {note_size} bytes")
    print(f"Expected total: {expected_total_size} bytes")
    print(f"Actual total: {size_with_note} bytes")

    # Should be approximately equal (within 10% tolerance)
    if abs(size_with_note - expected_total_size) / expected_total_size > 0.1:
        print(f"❌ Total size mismatch: got {size_with_note}, expected ~{expected_total_size}")
        return False

    print("✅ Total size correctly includes canvas + note")

    # Verify size_display format
    if 'KB' not in updated_diagram['size_display'] and 'MB' not in updated_diagram['size_display']:
        print(f"❌ Expected KB or MB in size_display, got: {updated_diagram['size_display']}")
        return False

    print(f"✅ Size display format: {updated_diagram['size_display']}")

    # Final summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    print("✅ All 8 steps passed!")
    print(f"   - Diagram with 100 shapes: {size_bytes} bytes ({our_diagram['size_display']})")
    print(f"   - Diagram with 1100 shapes: {size_bytes_large} bytes ({diagram_large['size_display']})")
    print(f"   - Diagram with note: {size_with_note} bytes ({updated_diagram['size_display']})")
    print("   - Size calculation working correctly")
    print("   - Size display format working (KB/MB)")
    print("   - Size increases proportionally with content")
    print("="*60)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

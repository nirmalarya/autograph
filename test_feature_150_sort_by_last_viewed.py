"""
Test Feature #150: Diagram sorting by last viewed

This test verifies that diagrams can be sorted by last_viewed_at timestamp,
showing the most recently viewed diagrams first.

Test Steps:
1. Register a test user
2. Login to get access token
3. Create diagram A
4. Create diagram B
5. Create diagram C
6. View diagram C (updates last_accessed_at)
7. View diagram A (updates last_accessed_at)
8. View diagram B (updates last_accessed_at)
9. List diagrams sorted by last_viewed (desc)
10. Verify order: B, A, C (most recent first)
11. List diagrams sorted by last_viewed (asc)
12. Verify order: C, A, B (oldest first)
"""

import requests
import time
import sys

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_feature_150():
    """Test diagram sorting by last viewed."""
    
    print("=" * 80)
    print("FEATURE #150: DIAGRAM SORTING BY LAST VIEWED")
    print("=" * 80)
    
    # Test 1: Register user
    print("\n[Test 1] Registering test user...")
    email = f"test_sort_viewed_{int(time.time())}@example.com"
    password = "TestPassword123!"
    
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Sort User"
        }
    )
    
    if register_response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {register_response.status_code}")
        print(f"Response: {register_response.text}")
        return False
    
    print(f"✅ User registered: {email}")
    
    # Test 2: Login
    print("\n[Test 2] Logging in...")
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    access_token = login_data.get("access_token")
    
    if not access_token:
        print("❌ Missing access_token in login response")
        return False
    
    # Decode JWT to get user_id
    import json
    import base64
    try:
        # JWT format: header.payload.signature
        payload = access_token.split('.')[1]
        # Add padding if needed
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        decoded = json.loads(base64.b64decode(payload))
        user_id = decoded.get('sub')
    except Exception as e:
        print(f"❌ Failed to decode JWT: {e}")
        return False
    
    if not user_id:
        print("❌ Missing user_id in JWT payload")
        return False
    
    print(f"✅ Login successful")
    print(f"   User ID: {user_id}")
    
    headers = {
        "X-User-ID": user_id,
        "Authorization": f"Bearer {access_token}"
    }
    
    # Test 3: Create diagram A
    print("\n[Test 3] Creating diagram A...")
    create_a_response = requests.post(
        f"{BASE_URL}/",
        headers=headers,
        json={
            "title": "Diagram A",
            "file_type": "canvas"
        }
    )
    
    if create_a_response.status_code != 200:
        print(f"❌ Failed to create diagram A: {create_a_response.status_code}")
        print(f"Response: {create_a_response.text}")
        return False
    
    diagram_a = create_a_response.json()
    diagram_a_id = diagram_a.get("id")
    
    if not diagram_a_id:
        print("❌ Missing diagram ID in response")
        return False
    
    print(f"✅ Diagram A created: {diagram_a_id}")
    
    # Small delay to ensure different timestamps
    time.sleep(0.5)
    
    # Test 4: Create diagram B
    print("\n[Test 4] Creating diagram B...")
    create_b_response = requests.post(
        f"{BASE_URL}/",
        headers=headers,
        json={
            "title": "Diagram B",
            "file_type": "canvas"
        }
    )
    
    if create_b_response.status_code != 200:
        print(f"❌ Failed to create diagram B: {create_b_response.status_code}")
        print(f"Response: {create_b_response.text}")
        return False
    
    diagram_b = create_b_response.json()
    diagram_b_id = diagram_b.get("id")
    
    if not diagram_b_id:
        print("❌ Missing diagram ID in response")
        return False
    
    print(f"✅ Diagram B created: {diagram_b_id}")
    
    # Small delay to ensure different timestamps
    time.sleep(0.5)
    
    # Test 5: Create diagram C
    print("\n[Test 5] Creating diagram C...")
    create_c_response = requests.post(
        f"{BASE_URL}/",
        headers=headers,
        json={
            "title": "Diagram C",
            "file_type": "canvas"
        }
    )
    
    if create_c_response.status_code != 200:
        print(f"❌ Failed to create diagram C: {create_c_response.status_code}")
        print(f"Response: {create_c_response.text}")
        return False
    
    diagram_c = create_c_response.json()
    diagram_c_id = diagram_c.get("id")
    
    if not diagram_c_id:
        print("❌ Missing diagram ID in response")
        return False
    
    print(f"✅ Diagram C created: {diagram_c_id}")
    
    # Small delay before viewing
    time.sleep(0.5)
    
    # Test 6: View diagram C
    print("\n[Test 6] Viewing diagram C...")
    view_c_response = requests.get(
        f"{BASE_URL}/{diagram_c_id}",
        headers=headers
    )
    
    if view_c_response.status_code != 200:
        print(f"❌ Failed to view diagram C: {view_c_response.status_code}")
        print(f"Response: {view_c_response.text}")
        return False
    
    view_c_data = view_c_response.json()
    print(f"✅ Diagram C viewed")
    print(f"   View count: {view_c_data.get('view_count', 0)}")
    print(f"   Last accessed: {view_c_data.get('last_accessed_at', 'N/A')}")
    
    # Small delay to ensure different timestamps
    time.sleep(0.5)
    
    # Test 7: View diagram A
    print("\n[Test 7] Viewing diagram A...")
    view_a_response = requests.get(
        f"{BASE_URL}/{diagram_a_id}",
        headers=headers
    )
    
    if view_a_response.status_code != 200:
        print(f"❌ Failed to view diagram A: {view_a_response.status_code}")
        print(f"Response: {view_a_response.text}")
        return False
    
    view_a_data = view_a_response.json()
    print(f"✅ Diagram A viewed")
    print(f"   View count: {view_a_data.get('view_count', 0)}")
    print(f"   Last accessed: {view_a_data.get('last_accessed_at', 'N/A')}")
    
    # Small delay to ensure different timestamps
    time.sleep(0.5)
    
    # Test 8: View diagram B
    print("\n[Test 8] Viewing diagram B...")
    view_b_response = requests.get(
        f"{BASE_URL}/{diagram_b_id}",
        headers=headers
    )
    
    if view_b_response.status_code != 200:
        print(f"❌ Failed to view diagram B: {view_b_response.status_code}")
        print(f"Response: {view_b_response.text}")
        return False
    
    view_b_data = view_b_response.json()
    print(f"✅ Diagram B viewed")
    print(f"   View count: {view_b_data.get('view_count', 0)}")
    print(f"   Last accessed: {view_b_data.get('last_accessed_at', 'N/A')}")
    
    # Small delay before listing
    time.sleep(0.5)
    
    # Test 9: List diagrams sorted by last_viewed (desc - most recent first)
    print("\n[Test 9] Listing diagrams sorted by last_viewed (desc)...")
    list_desc_response = requests.get(
        f"{BASE_URL}/",
        headers=headers,
        params={
            "sort_by": "last_viewed",
            "sort_order": "desc"
        }
    )
    
    if list_desc_response.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_desc_response.status_code}")
        print(f"Response: {list_desc_response.text}")
        return False
    
    list_desc_data = list_desc_response.json()
    diagrams_desc = list_desc_data.get("diagrams", [])
    
    if len(diagrams_desc) < 3:
        print(f"❌ Expected at least 3 diagrams, got {len(diagrams_desc)}")
        return False
    
    print(f"✅ Diagrams listed (sorted by last_viewed desc)")
    print(f"   Total diagrams: {list_desc_data.get('total', 0)}")
    
    # Test 10: Verify order: B, A, C (most recent first)
    print("\n[Test 10] Verifying sort order (desc - most recent first)...")
    
    # Get the first 3 diagrams (they should be B, A, C)
    first_three = diagrams_desc[:3]
    
    print(f"   Order:")
    for i, diagram in enumerate(first_three):
        print(f"     {i+1}. {diagram.get('title')} (ID: {diagram.get('id')[:8]}..., Last accessed: {diagram.get('last_accessed_at', 'N/A')})")
    
    # Verify the order
    if (first_three[0].get('id') == diagram_b_id and
        first_three[1].get('id') == diagram_a_id and
        first_three[2].get('id') == diagram_c_id):
        print(f"✅ Sort order correct: B, A, C (most recent first)")
    else:
        print(f"❌ Sort order incorrect!")
        print(f"   Expected: B ({diagram_b_id[:8]}...), A ({diagram_a_id[:8]}...), C ({diagram_c_id[:8]}...)")
        print(f"   Got: {first_three[0].get('title')} ({first_three[0].get('id')[:8]}...), "
              f"{first_three[1].get('title')} ({first_three[1].get('id')[:8]}...), "
              f"{first_three[2].get('title')} ({first_three[2].get('id')[:8]}...)")
        return False
    
    # Test 11: List diagrams sorted by last_viewed (asc - oldest first)
    print("\n[Test 11] Listing diagrams sorted by last_viewed (asc)...")
    list_asc_response = requests.get(
        f"{BASE_URL}/",
        headers=headers,
        params={
            "sort_by": "last_viewed",
            "sort_order": "asc"
        }
    )
    
    if list_asc_response.status_code != 200:
        print(f"❌ Failed to list diagrams: {list_asc_response.status_code}")
        print(f"Response: {list_asc_response.text}")
        return False
    
    list_asc_data = list_asc_response.json()
    diagrams_asc = list_asc_data.get("diagrams", [])
    
    if len(diagrams_asc) < 3:
        print(f"❌ Expected at least 3 diagrams, got {len(diagrams_asc)}")
        return False
    
    print(f"✅ Diagrams listed (sorted by last_viewed asc)")
    
    # Test 12: Verify order: C, A, B (oldest first)
    print("\n[Test 12] Verifying sort order (asc - oldest first)...")
    
    # Get the first 3 diagrams (they should be C, A, B)
    first_three_asc = diagrams_asc[:3]
    
    print(f"   Order:")
    for i, diagram in enumerate(first_three_asc):
        print(f"     {i+1}. {diagram.get('title')} (ID: {diagram.get('id')[:8]}..., Last accessed: {diagram.get('last_accessed_at', 'N/A')})")
    
    # Verify the order
    if (first_three_asc[0].get('id') == diagram_c_id and
        first_three_asc[1].get('id') == diagram_a_id and
        first_three_asc[2].get('id') == diagram_b_id):
        print(f"✅ Sort order correct: C, A, B (oldest first)")
    else:
        print(f"❌ Sort order incorrect!")
        print(f"   Expected: C ({diagram_c_id[:8]}...), A ({diagram_a_id[:8]}...), B ({diagram_b_id[:8]}...)")
        print(f"   Got: {first_three_asc[0].get('title')} ({first_three_asc[0].get('id')[:8]}...), "
              f"{first_three_asc[1].get('title')} ({first_three_asc[1].get('id')[:8]}...), "
              f"{first_three_asc[2].get('title')} ({first_three_asc[2].get('id')[:8]}...)")
        return False
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nFeature #150 Summary:")
    print("- Diagram sorting by last_viewed works correctly")
    print("- Descending order shows most recently viewed first")
    print("- Ascending order shows oldest viewed first")
    print("- last_accessed_at timestamp updates on diagram view")
    print("- Sort order is accurate and consistent")
    
    return True


if __name__ == "__main__":
    try:
        success = test_feature_150()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

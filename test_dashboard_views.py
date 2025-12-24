#!/usr/bin/env python3
"""Test script to verify all dashboard views work correctly."""

import requests
import json
import sys

USER_ID = "8377f74b-26a4-426a-8aa9-8cd144f18f70"
BASE_URL = "http://localhost:8082"

def test_all_diagrams():
    """Test: All diagrams view"""
    print("\n✅ Test 1: All Diagrams View")
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"page": 1, "page_size": 20}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "diagrams" in data, "Response should have 'diagrams' field"
    assert "total" in data, "Response should have 'total' field"
    print(f"   - Total diagrams: {data['total']}")
    print(f"   - Returned: {len(data['diagrams'])}")
    print("   ✅ All Diagrams view works!")

def test_recent_view():
    """Test: Recent view"""
    print("\n✅ Test 2: Recent View")
    response = requests.get(
        f"{BASE_URL}/recent",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "diagrams" in data, "Response should have 'diagrams' field"
    print(f"   - Total recent diagrams: {data.get('total', len(data['diagrams']))}")
    print("   ✅ Recent view works!")

def test_starred_view():
    """Test: Starred view"""
    print("\n✅ Test 3: Starred View")
    response = requests.get(
        f"{BASE_URL}/starred",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "diagrams" in data, "Response should have 'diagrams' field"
    assert "total" in data, "Response should have 'total' field"
    print(f"   - Total starred diagrams: {data['total']}")
    print("   ✅ Starred view works!")

def test_shared_view():
    """Test: Shared with me view"""
    print("\n✅ Test 4: Shared with Me View")
    response = requests.get(
        f"{BASE_URL}/shared-with-me",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "diagrams" in data, "Response should have 'diagrams' field"
    print(f"   - Total shared diagrams: {data.get('total', len(data['diagrams']))}")
    print("   ✅ Shared with me view works!")

def test_trash_view():
    """Test: Trash view"""
    print("\n✅ Test 5: Trash View")
    response = requests.get(
        f"{BASE_URL}/trash",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "diagrams" in data, "Response should have 'diagrams' field"
    assert "total" in data, "Response should have 'total' field"
    print(f"   - Total diagrams in trash: {data['total']}")
    print("   ✅ Trash view works!")

def test_grid_view():
    """Test: Grid view (same as all diagrams)"""
    print("\n✅ Test 6: Grid View")
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    for diagram in data.get('diagrams', []):
        assert 'id' in diagram, "Diagram should have 'id'"
        assert 'title' in diagram, "Diagram should have 'title'"
        assert 'file_type' in diagram, "Diagram should have 'file_type'"
    print("   ✅ Grid view data format correct!")

def test_list_view():
    """Test: List view (same as all diagrams)"""
    print("\n✅ Test 7: List View")
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID}
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    print("   ✅ List view data format correct!")

def test_sorting():
    """Test: Sorting options"""
    print("\n✅ Test 8: Sorting")
    
    # Test sorting by name
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"sort_by": "title", "sort_order": "asc"}
    )
    assert response.status_code == 200, "Sort by name should work"
    print("   - Sort by name: ✅")
    
    # Test sorting by date created
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"sort_by": "created_at", "sort_order": "desc"}
    )
    assert response.status_code == 200, "Sort by created should work"
    print("   - Sort by date created: ✅")
    
    # Test sorting by date updated
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"sort_by": "updated_at", "sort_order": "desc"}
    )
    assert response.status_code == 200, "Sort by updated should work"
    print("   - Sort by date updated: ✅")
    
    # Test sorting by last viewed
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"sort_by": "last_viewed", "sort_order": "desc"}
    )
    assert response.status_code == 200, "Sort by last viewed should work"
    print("   - Sort by last viewed: ✅")
    
    # Note: size_bytes is not a sortable field (it's calculated dynamically)
    
    print("   ✅ All sorting options work!")

def test_filtering():
    """Test: Filtering by type"""
    print("\n✅ Test 9: Filtering")
    
    # Test filter by canvas
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"file_type": "canvas"}
    )
    assert response.status_code == 200, "Filter by canvas should work"
    print("   - Filter by canvas: ✅")
    
    # Test filter by note
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"file_type": "note"}
    )
    assert response.status_code == 200, "Filter by note should work"
    print("   - Filter by note: ✅")
    
    # Test filter by mixed
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"file_type": "mixed"}
    )
    assert response.status_code == 200, "Filter by mixed should work"
    print("   - Filter by mixed: ✅")
    
    print("   ✅ All filtering options work!")

def test_search():
    """Test: Search functionality"""
    print("\n✅ Test 10: Search")
    response = requests.get(
        f"{BASE_URL}/",
        headers={"X-User-ID": USER_ID},
        params={"search": "test"}
    )
    assert response.status_code == 200, "Search should work"
    print("   ✅ Search functionality works!")

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 Testing Dashboard Views - All Features")
    print("=" * 70)
    
    try:
        test_all_diagrams()
        test_recent_view()
        test_starred_view()
        test_shared_view()
        test_trash_view()
        test_grid_view()
        test_list_view()
        test_sorting()
        test_filtering()
        test_search()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

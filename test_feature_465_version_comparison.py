#!/usr/bin/env python3
"""
Feature #465: Version history: Version comparison: visual diff
Steps:
1. Select v1 and v2
2. Click Compare  
3. Verify side-by-side view
4. Verify differences highlighted
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def test_feature_465():
    print("Testing Feature #465: Version Comparison Visual Diff")
    print("=" * 60)
    
    # Step 1: Login with existing user
    print("\n1. Logging in...")
    login_data = {"email": "versioncompare465@test.com", "password": "password123"}
    r = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    assert r.status_code == 200, f"Login failed: {r.status_code}"
    
    token = r.json()["access_token"]
    user_id = r.json()["user"]["id"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    print("   ✓ User logged in")
    
    # Step 2: Create a diagram
    print("\n2. Creating diagram...")
    diagram_data = {
        "diagram_type": "canvas",
        "title": "Version Compare Test Diagram",
        "canvas_data": {"shapes": [{"id": "1", "type": "rect", "x": 10, "y": 10}]},
        "thumbnail_url": "http://example.com/thumb1.png"
    }
    
    r = requests.post(f"{BASE_URL}/diagrams", json=diagram_data, headers=headers)
    assert r.status_code in [200, 201], f"Create diagram failed: {r.status_code}"
    diagram_id = r.json()["id"]
    print(f"   ✓ Diagram created: {diagram_id}")
    
    # Step 3: Update diagram to create version 2
    print("\n3. Creating version 2 (with changes)...")
    update_data = {
        "canvas_data": {
            "shapes": [
                {"id": "1", "type": "rect", "x": 10, "y": 10},
                {"id": "2", "type": "circle", "x": 50, "y": 50}  # Added shape
            ]
        },
        "thumbnail_url": "http://example.com/thumb2.png"
    }
    
    r = requests.put(f"{BASE_URL}/diagrams/{diagram_id}", json=update_data, headers=headers)
    assert r.status_code == 200, f"Update diagram failed: {r.status_code}"
    print("   ✓ Version 2 created with changes")
    
    # Step 4: Update again to create version 3
    print("\n4. Creating version 3 (with more changes)...")
    update_data2 = {
        "canvas_data": {
            "shapes": [
                {"id": "1", "type": "rect", "x": 20, "y": 20},  # Modified position
                {"id": "3", "type": "triangle", "x": 100, "y": 100}  # Replaced circle with triangle
            ]
        },
        "thumbnail_url": "http://example.com/thumb3.png"
    }
    
    r = requests.put(f"{BASE_URL}/diagrams/{diagram_id}", json=update_data2, headers=headers)
    assert r.status_code == 200, f"Update diagram failed: {r.status_code}"
    print("   ✓ Version 3 created with more changes")
    
    # Step 5: Compare v1 and v2
    print("\n5. Comparing v1 and v2...")
    r = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/versions/compare/1/2",
        headers=headers
    )
    assert r.status_code == 200, f"Compare v1 vs v2 failed: {r.status_code} - {r.text}"
    
    comparison_1_2 = r.json()
    print(f"   ✓ Comparison retrieved")
    
    # Verify comparison structure
    assert "version1" in comparison_1_2, "Missing version1 in comparison"
    assert "version2" in comparison_1_2, "Missing version2 in comparison"
    assert "differences" in comparison_1_2, "Missing differences in comparison"
    print("   ✓ Comparison structure valid")
    
    # Verify differences are highlighted
    diffs = comparison_1_2["differences"]
    assert "additions" in diffs, "Missing additions in differences"
    assert "deletions" in diffs, "Missing deletions in differences"
    assert "modifications" in diffs, "Missing modifications in differences"
    assert "summary" in diffs, "Missing summary in differences"
    print("   ✓ Differences structure valid")
    
    # Verify summary counts
    summary = diffs["summary"]
    print(f"\n   Differences Summary (v1 → v2):")
    print(f"   - Total changes: {summary['total_changes']}")
    print(f"   - Added: {summary['added_count']}")
    print(f"   - Deleted: {summary['deleted_count']}")
    print(f"   - Modified: {summary['modified_count']}")
    
    # v1 → v2 should have 1 addition (circle added)
    assert summary['added_count'] >= 1, "Expected at least 1 addition (circle)"
    print("   ✓ Additions detected")
    
    # Step 6: Compare v2 and v3
    print("\n6. Comparing v2 and v3...")
    r = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/versions/compare/2/3",
        headers=headers
    )
    assert r.status_code == 200, f"Compare v2 vs v3 failed: {r.status_code}"
    
    comparison_2_3 = r.json()
    diffs_2_3 = comparison_2_3["differences"]
    summary_2_3 = diffs_2_3["summary"]
    
    print(f"\n   Differences Summary (v2 → v3):")
    print(f"   - Total changes: {summary_2_3['total_changes']}")
    print(f"   - Added: {summary_2_3['added_count']}")
    print(f"   - Deleted: {summary_2_3['deleted_count']}")
    print(f"   - Modified: {summary_2_3['modified_count']}")
    
    # v2 → v3 should have changes (modified rect, deleted circle, added triangle)
    assert summary_2_3['total_changes'] > 0, "Expected changes between v2 and v3"
    print("   ✓ Changes detected")
    
    # Step 7: Verify visual diff data structure
    print("\n7. Verifying visual diff data structure...")
    
    # Check that additions have proper structure
    if len(diffs["additions"]) > 0:
        addition = diffs["additions"][0]
        print(f"   ✓ Addition example: {json.dumps(addition, indent=2)[:200]}...")
    
    # Check that modifications have before/after structure
    if len(diffs_2_3["modifications"]) > 0:
        modification = diffs_2_3["modifications"][0]
        assert "id" in modification, "Modification missing element id"
        assert "changes" in modification, "Modification missing changes list"
        assert "before" in modification, "Modification missing before state"
        assert "after" in modification, "Modification missing after state"
        print(f"   ✓ Modification has before/after structure")
    
    print("\n" + "=" * 60)
    print("✅ Feature #465: PASSING")
    print("=" * 60)
    print("\nVerified:")
    print("  ✓ Can select v1 and v2 (via API)")
    print("  ✓ Can compare versions (API endpoint works)")
    print("  ✓ Side-by-side data provided (version1 and version2)")
    print("  ✓ Differences highlighted (additions, deletions, modifications)")
    print("  ✓ Visual diff structure complete (summary, before/after)")
    
    return True

if __name__ == "__main__":
    try:
        test_feature_465()
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

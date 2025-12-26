#!/usr/bin/env python3
"""
Feature #441: Comment Search - Full-text search
Test the search query parameter for filtering comments by content.
"""

import requests
import uuid
import psycopg2

# Configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password"
}


def verify_email(email):
    """Mark user email as verified in database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Email is stored as lowercase in the database
        cur.execute(
            "UPDATE users SET is_verified = true WHERE LOWER(email) = LOWER(%s)",
            (email,)
        )
        rows_affected = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        print(f"  → Email verified for {email} (rows affected: {rows_affected})")
    except Exception as e:
        print(f"  → Failed to verify email: {e}")

def test_comment_search():
    """Test full-text search in comments."""

    print("="*60)
    print("Feature #441: Comment Search - Full-text search")
    print("="*60)

    # Step 1: Register a test user
    print("\n1. Registering test user...")
    import time
    timestamp = int(time.time() * 1000)
    test_email = f"search_test_{timestamp}@example.com"
    test_password = "SecurePass123!"

    register_response = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "full_name": "Search Test User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Failed to register: {register_response.status_code}")
        print(register_response.text)
        return False

    user_id = register_response.json()["id"]
    print(f"✅ User registered: {test_email}")

    # Verify email in database
    verify_email(test_email)

    # Step 2: Login
    print("\n2. Logging in...")
    login_response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            "email": test_email,
            "password": test_password
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Failed to login: {login_response.status_code}")
        print(login_response.text)
        return False

    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print(f"✅ User logged in")

    # Step 3: Create a diagram
    print("\n3. Creating a test diagram...")
    diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers=headers,
        json={
            "title": "Comment Search Test Diagram",
            "type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )

    if diagram_response.status_code not in [200, 201]:
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(diagram_response.text)
        return False

    diagram_id = diagram_response.json()["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 4: Add 10 comments with diverse content
    print("\n4. Adding 10 comments with diverse content...")
    comment_contents = [
        "This diagram needs a database schema update",
        "Let's discuss the authentication flow here",
        "The database connection is slow",
        "Great work on the UI design!",
        "We should add more database indexes",
        "The API endpoint needs validation",
        "Database query optimization required",
        "Nice color scheme in the diagram",
        "The database migration script is ready",
        "Frontend integration looks good"
    ]

    comment_ids = []
    for i, content in enumerate(comment_contents):
        comment_response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
            headers={"X-User-ID": user_id},
            json={
                "content": content,
                "position_x": 100.0 + i * 10,
                "position_y": 100.0 + i * 10
            }
        )

        if comment_response.status_code != 201:
            print(f"❌ Failed to create comment {i+1}: {comment_response.status_code}")
            print(comment_response.text)
            return False

        comment_ids.append(comment_response.json()["id"])

    print(f"✅ Created {len(comment_ids)} comments")

    # Step 5: Search for "database" (should match 5 comments)
    print("\n5. Searching for 'database'...")
    search_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers={"X-User-ID": user_id},
        params={"search": "database"}
    )

    if search_response.status_code != 200:
        print(f"❌ Failed to search comments: {search_response.status_code}")
        print(search_response.text)
        return False

    search_results = search_response.json()
    matched_comments = search_results["comments"]

    print(f"   Found {len(matched_comments)} comments containing 'database'")

    # Verify we found exactly 5 comments containing "database"
    expected_count = 5
    if len(matched_comments) != expected_count:
        print(f"❌ Expected {expected_count} comments, found {len(matched_comments)}")
        for comment in matched_comments:
            print(f"   - {comment['content']}")
        return False

    # Verify all matched comments contain "database" (case-insensitive)
    for comment in matched_comments:
        if "database" not in comment["content"].lower():
            print(f"❌ Comment doesn't contain 'database': {comment['content']}")
            return False

    print("✅ All matched comments contain 'database'")

    # Step 6: Verify search results show correct comments
    print("\n6. Verifying search results...")
    expected_comments = [
        "This diagram needs a database schema update",
        "The database connection is slow",
        "We should add more database indexes",
        "Database query optimization required",
        "The database migration script is ready"
    ]

    found_contents = [c["content"] for c in matched_comments]
    for expected in expected_comments:
        if expected not in found_contents:
            print(f"❌ Expected comment not found: {expected}")
            print(f"   Found: {found_contents}")
            return False

    print("✅ All expected comments found in search results")

    # Step 7: Verify other comments are hidden
    print("\n7. Verifying other comments are hidden...")
    hidden_comments = [
        "Let's discuss the authentication flow here",
        "Great work on the UI design!",
        "The API endpoint needs validation",
        "Nice color scheme in the diagram",
        "Frontend integration looks good"
    ]

    for hidden in hidden_comments:
        if hidden in found_contents:
            print(f"❌ Comment should be hidden but was found: {hidden}")
            return False

    print("✅ Non-matching comments are correctly hidden")

    # Step 8: Test case-insensitive search
    print("\n8. Testing case-insensitive search...")
    case_search_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers={"X-User-ID": user_id},
        params={"search": "DATABASE"}
    )

    if case_search_response.status_code != 200:
        print(f"❌ Failed to search with uppercase: {case_search_response.status_code}")
        return False

    case_results = case_search_response.json()
    if len(case_results["comments"]) != expected_count:
        print(f"❌ Case-insensitive search failed: expected {expected_count}, got {len(case_results['comments'])}")
        return False

    print("✅ Case-insensitive search works correctly")

    # Step 9: Test partial word search
    print("\n9. Testing partial word search...")
    partial_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers={"X-User-ID": user_id},
        params={"search": "datab"}
    )

    if partial_response.status_code != 200:
        print(f"❌ Failed to search with partial word: {partial_response.status_code}")
        return False

    partial_results = partial_response.json()
    if len(partial_results["comments"]) != expected_count:
        print(f"❌ Partial word search failed: expected {expected_count}, got {len(partial_results['comments'])}")
        return False

    print("✅ Partial word search works correctly")

    # Step 10: Test search with no results
    print("\n10. Testing search with no results...")
    no_results_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers={"X-User-ID": user_id},
        params={"search": "nonexistent"}
    )

    if no_results_response.status_code != 200:
        print(f"❌ Failed to search for non-existent term: {no_results_response.status_code}")
        return False

    no_results = no_results_response.json()
    if len(no_results["comments"]) != 0:
        print(f"❌ Expected 0 results, got {len(no_results['comments'])}")
        return False

    print("✅ Search with no results returns empty list")

    # Step 11: Test search without search parameter (should return all)
    print("\n11. Testing without search parameter...")
    all_comments_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers={"X-User-ID": user_id}
    )

    if all_comments_response.status_code != 200:
        print(f"❌ Failed to get all comments: {all_comments_response.status_code}")
        return False

    all_comments = all_comments_response.json()
    if len(all_comments["comments"]) != 10:
        print(f"❌ Expected 10 comments, got {len(all_comments['comments'])}")
        return False

    print("✅ Without search parameter, all comments are returned")

    print("\n" + "="*60)
    print("✅ Feature #441: Comment Search - ALL TESTS PASSED")
    print("="*60)
    return True


if __name__ == "__main__":
    try:
        success = test_comment_search()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

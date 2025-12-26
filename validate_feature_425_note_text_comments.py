#!/usr/bin/env python3
"""
Validation script for Feature #425: Comments: Add comment to note text selection

This script validates:
1. Comment model has text selection fields (text_start, text_end, text_content)
2. POST /comments endpoint accepts text selection parameters
3. GET /comments endpoint returns text selection data
4. Frontend has note comment UI action
5. Comment dialog shows selected text
"""

import requests
import json
import sys
import psycopg2

BASE_URL = "http://localhost:8080"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "TestPassword123!"

def check_database_schema():
    """Verify comment table has text selection columns."""
    print("\n1. Checking database schema...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="autograph",
            user="autograph",
            password="autograph_password",
            port=5432
        )
        cursor = conn.cursor()

        # Check for text selection columns
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'comments'
            AND column_name IN ('text_start', 'text_end', 'text_content')
            ORDER BY column_name;
        """)

        columns = cursor.fetchall()
        cursor.close()
        conn.close()

        if len(columns) >= 3:
            print("✅ Comment table has text selection fields:")
            for col in columns:
                print(f"   - {col[0]}: {col[1]}")
            return True
        else:
            print(f"❌ Missing text selection columns. Found: {columns}")
            return False

    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def register_and_login():
    """Register and login test user."""
    print("\n2. Setting up test user...")

    # Try to register (might fail if user exists)
    try:
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "full_name": "Test User"
        })
    except:
        pass

    # Login
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    })

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logged in as {TEST_USER_EMAIL}")
        return data['access_token'], data['user_id']
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None, None

def create_test_diagram(token, user_id):
    """Create a test diagram."""
    print("\n3. Creating test diagram...")

    response = requests.post(
        f"{BASE_URL}/diagrams",
        headers={"X-User-ID": user_id},
        json={
            "title": "Note Comment Test Diagram",
            "type": "note",
            "canvas_data": {"shapes": []},
            "note_content": "This is a test note with some text to comment on."
        }
    )

    if response.status_code == 201:
        diagram_id = response.json()['id']
        print(f"✅ Created diagram: {diagram_id}")
        return diagram_id
    else:
        print(f"❌ Failed to create diagram: {response.status_code}")
        return None

def test_note_text_comment(token, user_id, diagram_id):
    """Test creating a comment on note text selection."""
    print("\n4. Testing note text selection comment creation...")

    # Create comment with text selection
    response = requests.post(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "X-User-ID": user_id,
            "Content-Type": "application/json"
        },
        json={
            "content": "This is a comment on the selected text",
            "element_id": "note_1",
            "text_start": 10,
            "text_end": 24,
            "text_content": "test note with",
            "is_private": False
        }
    )

    if response.status_code == 201:
        comment = response.json()
        print(f"✅ Created note text comment: {comment['id']}")
        return comment['id']
    else:
        print(f"❌ Failed to create comment: {response.status_code} - {response.text}")
        return None

def verify_comment_retrieval(token, user_id, diagram_id, comment_id):
    """Verify comment can be retrieved with text selection data."""
    print("\n5. Verifying comment retrieval...")

    response = requests.get(
        f"{BASE_URL}/diagrams/{diagram_id}/comments",
        headers={"X-User-ID": user_id}
    )

    if response.status_code == 200:
        data = response.json()
        comments = data.get('comments', [])

        # Find our comment
        comment = next((c for c in comments if c['id'] == comment_id), None)

        if comment:
            # Check text selection fields
            has_text_start = comment.get('text_start') is not None
            has_text_end = comment.get('text_end') is not None
            has_text_content = comment.get('text_content') is not None

            if has_text_start and has_text_end and has_text_content:
                print(f"✅ Comment has text selection data:")
                print(f"   - text_start: {comment['text_start']}")
                print(f"   - text_end: {comment['text_end']}")
                print(f"   - text_content: {comment['text_content']}")
                return True
            else:
                print(f"❌ Comment missing text selection fields:")
                print(f"   - text_start: {has_text_start}")
                print(f"   - text_end: {has_text_end}")
                print(f"   - text_content: {has_text_content}")
                return False
        else:
            print(f"❌ Comment {comment_id} not found in list")
            return False
    else:
        print(f"❌ Failed to retrieve comments: {response.status_code}")
        return False

def check_frontend_implementation():
    """Check if frontend files have been updated."""
    print("\n6. Checking frontend implementation...")

    try:
        # Check TLDrawCanvas.tsx has onAddNoteComment
        with open('services/frontend/app/canvas/[id]/TLDrawCanvas.tsx', 'r') as f:
            content = f.read()
            has_prop = 'onAddNoteComment' in content
            has_action = 'add-note-comment' in content

            if has_prop and has_action:
                print("✅ TLDrawCanvas has note comment action")
            else:
                print(f"❌ TLDrawCanvas missing implementation (prop: {has_prop}, action: {has_action})")
                return False

        # Check page.tsx has handler
        with open('services/frontend/app/canvas/[id]/page.tsx', 'r') as f:
            content = f.read()
            has_handler = 'handleAddNoteComment' in content
            has_state = 'commentTextStart' in content
            has_dialog_update = 'Add Comment to Note Text' in content

            if has_handler and has_state and has_dialog_update:
                print("✅ Page component has note comment handler and UI")
            else:
                print(f"❌ Page component missing implementation:")
                print(f"   - Handler: {has_handler}")
                print(f"   - State: {has_state}")
                print(f"   - Dialog: {has_dialog_update}")
                return False

        return True

    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Feature #425 Validation: Note Text Selection Comments")
    print("=" * 60)

    results = []

    # 1. Database schema
    results.append(("Database Schema", check_database_schema()))

    # 2. Register and login
    token, user_id = register_and_login()
    if not token:
        print("\n❌ Cannot proceed without authentication")
        sys.exit(1)
    results.append(("User Authentication", True))

    # 3. Create test diagram
    diagram_id = create_test_diagram(token, user_id)
    if not diagram_id:
        print("\n❌ Cannot proceed without diagram")
        sys.exit(1)
    results.append(("Diagram Creation", True))

    # 4. Create note text comment
    comment_id = test_note_text_comment(token, user_id, diagram_id)
    if comment_id:
        results.append(("Note Text Comment Creation", True))

        # 5. Verify comment retrieval
        results.append(("Comment Retrieval", verify_comment_retrieval(token, user_id, diagram_id, comment_id)))
    else:
        results.append(("Note Text Comment Creation", False))
        results.append(("Comment Retrieval", False))

    # 6. Frontend implementation
    results.append(("Frontend Implementation", check_frontend_implementation()))

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n🎉 All validation checks passed!")
        print("Feature #425 is working correctly!")
        return 0
    else:
        print("\n⚠️  Some validation checks failed.")
        print("Please review the failures above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

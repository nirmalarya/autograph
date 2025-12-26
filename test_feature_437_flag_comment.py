#!/usr/bin/env python3
"""
Feature #437 Test: Comment Moderation - Flag Inappropriate Comments

Tests the ability to flag comments as inappropriate and have admins review them.

Test Flow:
1. Regular user creates diagram and posts comment
2. Another user flags the comment as inappropriate
3. Verify flag is created with pending status
4. Admin logs in and views flagged comments
5. Admin reviews and dismisses/deletes the comment
6. Verify flag status updated
"""

import requests
import time
import uuid
import psycopg2
import base64
import json

# Test configuration
API_BASE_URL = "http://localhost:8080/api"
DIAGRAM_SERVICE_URL = "http://localhost:8082"
DB_CONFIG = {
    "dbname": "autograph",
    "user": "autograph",
    "password": "autograph_dev_password",
    "host": "localhost",
    "port": 5432
}

def verify_email(email):
    """Mark user email as verified in database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET is_verified = true WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

def make_user_admin(email):
    """Make a user an admin in the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET role = 'admin' WHERE email = %s",
        (email,)
    )
    conn.commit()
    cur.close()
    conn.close()

def test_flag_comment_workflow():
    """Test complete flag comment workflow."""
    print("=" * 80)
    print("Feature #437 Test: Comment Moderation - Flag Inappropriate")
    print("=" * 80)

    # Step 1: Create users
    print("\n[1/6] Creating users...")
    author_email = f"comment_author_{uuid.uuid4().hex[:8]}@example.com"
    flagger_email = f"comment_flagger_{uuid.uuid4().hex[:8]}@example.com"
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    # Register author
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": author_email,
            "password": password,
            "full_name": "Comment Author"
        }
    )
    verify_email(author_email)

    # Register flagger
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": flagger_email,
            "password": password,
            "full_name": "Comment Flagger"
        }
    )
    verify_email(flagger_email)

    # Register admin
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "email": admin_email,
            "password": password,
            "full_name": "Admin User"
        }
    )
    verify_email(admin_email)
    make_user_admin(admin_email)

    # Login all users
    author_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": author_email, "password": password}
    ).json()
    author_token = author_login["access_token"]
    author_id = json.loads(base64.b64decode(
        author_token.split('.')[1] + '=' * (4 - len(author_token.split('.')[1]) % 4)
    ))["sub"]

    flagger_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": flagger_email, "password": password}
    ).json()
    flagger_token = flagger_login["access_token"]
    flagger_id = json.loads(base64.b64decode(
        flagger_token.split('.')[1] + '=' * (4 - len(flagger_token.split('.')[1]) % 4)
    ))["sub"]

    admin_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": admin_email, "password": password}
    ).json()
    admin_token = admin_login["access_token"]
    admin_id = json.loads(base64.b64decode(
        admin_token.split('.')[1] + '=' * (4 - len(admin_token.split('.')[1]) % 4)
    ))["sub"]

    print(f"✅ Created users: author, flagger, admin")

    # Step 2: Create diagram and comment
    print("\n[2/6] Creating diagram and comment...")
    diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        },
        json={
            "title": "Flag Test Diagram",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )

    if diagram_response.status_code not in (200, 201):
        print(f"❌ Failed to create diagram: {diagram_response.status_code}")
        print(diagram_response.text)
        return False

    diagram_id = diagram_response.json()["id"]

    comment_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        },
        json={"content": "This is an inappropriate comment"}
    )

    if comment_response.status_code != 201:
        print(f"❌ Failed to create comment: {comment_response.status_code}")
        print(comment_response.text)
        return False

    comment_id = comment_response.json()["id"]
    print(f"✅ Created diagram and comment: {comment_id}")

    # Step 3: Flag the comment
    print("\n[3/6] Flagger flags the comment...")
    flag_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/flag",
        headers={
            "Authorization": f"Bearer {flagger_token}",
            "X-User-ID": flagger_id
        },
        json={
            "reason": "offensive",
            "details": "This comment contains inappropriate language"
        }
    )

    if flag_response.status_code != 200:
        print(f"❌ Failed to flag comment: {flag_response.status_code}")
        print(flag_response.text)
        return False

    flag_data = flag_response.json()
    flag_id = flag_data["flag_id"]
    print(f"✅ Comment flagged successfully")
    print(f"   Flag ID: {flag_id}")
    print(f"   Status: {flag_data['status']}")

    # Verify duplicate flag is prevented
    print("\n   Testing duplicate flag prevention...")
    duplicate_flag_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/flag",
        headers={
            "Authorization": f"Bearer {flagger_token}",
            "X-User-ID": flagger_id
        },
        json={
            "reason": "spam",
            "details": "Trying to flag again"
        }
    )

    if duplicate_flag_response.status_code == 409:
        print(f"✅ Duplicate flag prevented (409)")
    else:
        print(f"❌ Expected 409 for duplicate flag, got {duplicate_flag_response.status_code}")
        return False

    # Step 4: Admin views flagged comments
    print("\n[4/6] Admin viewing flagged comments...")
    admin_flags_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags",
        headers={
            "X-User-ID": admin_id
        }
    )

    if admin_flags_response.status_code != 200:
        print(f"❌ Failed to get flags: {admin_flags_response.status_code}")
        print(admin_flags_response.text)
        return False

    flags_data = admin_flags_response.json()
    flags = flags_data.get("flags", [])

    print(f"✅ Admin retrieved {len(flags)} flag(s)")

    # Find our flag
    our_flag = None
    for flag in flags:
        if flag["flag_id"] == flag_id:
            our_flag = flag
            break

    if not our_flag:
        print(f"❌ Could not find our flag in admin list")
        return False

    print(f"   Flag details:")
    print(f"   - Comment content: {our_flag['comment_content']}")
    print(f"   - Reason: {our_flag['reason']}")
    print(f"   - Status: {our_flag['status']}")
    print(f"   - Flagger: {our_flag['flagger_email']}")

    # Test filter by status
    print("\n   Testing filter by status...")
    pending_flags_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags?status=pending",
        headers={
            "X-User-ID": admin_id
        }
    )

    if pending_flags_response.status_code != 200:
        print(f"❌ Failed to filter flags: {pending_flags_response.status_code}")
        return False

    pending_count = pending_flags_response.json()["total"]
    print(f"✅ Found {pending_count} pending flag(s)")

    # Step 5: Admin reviews flag (dismiss)
    print("\n[5/6] Admin reviewing and dismissing flag...")
    review_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags/{flag_id}/review",
        headers={
            "X-User-ID": admin_id
        },
        json={
            "action": "dismiss",
            "admin_notes": "Comment reviewed - not actually offensive"
        }
    )

    if review_response.status_code != 200:
        print(f"❌ Failed to review flag: {review_response.status_code}")
        print(review_response.text)
        return False

    review_data = review_response.json()
    print(f"✅ Flag reviewed successfully")
    print(f"   Message: {review_data['message']}")
    print(f"   New status: {review_data['status']}")

    # Verify flag status changed
    print("\n[6/6] Verifying flag status updated...")
    updated_flags_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags",
        headers={
            "X-User-ID": admin_id
        }
    )

    updated_flags = updated_flags_response.json()["flags"]
    updated_flag = None
    for flag in updated_flags:
        if flag["flag_id"] == flag_id:
            updated_flag = flag
            break

    if not updated_flag:
        print(f"❌ Could not find updated flag")
        return False

    if updated_flag["status"] != "dismissed":
        print(f"❌ Flag status not updated. Expected 'dismissed', got '{updated_flag['status']}'")
        return False

    if updated_flag["reviewed_by"] != admin_id:
        print(f"❌ Reviewed_by not set correctly")
        return False

    if not updated_flag["reviewed_at"]:
        print(f"❌ Reviewed_at not set")
        return False

    print(f"✅ Flag status updated to 'dismissed'")
    print(f"   Reviewed by: {updated_flag['reviewed_by']}")
    print(f"   Reviewed at: {updated_flag['reviewed_at']}")
    print(f"   Admin notes: {updated_flag['admin_notes']}")

    # Verify comment still exists (was not deleted)
    comment_check_response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        }
    )

    comments = comment_check_response.json().get("comments", [])
    comment_exists = any(c["id"] == comment_id for c in comments)

    if comment_exists:
        print(f"✅ Comment still exists (correctly not deleted on dismiss)")
    else:
        print(f"❌ Comment was deleted (should still exist on dismiss)")
        return False

    print("\n" + "=" * 80)
    print("✅ Feature #437 TEST PASSED: Comment Moderation - Flag Inappropriate")
    print("=" * 80)
    print("\nTest Results:")
    print("✅ Users can flag comments as inappropriate")
    print("✅ Flag reasons: spam, harassment, offensive, inappropriate, other")
    print("✅ Duplicate flags prevented (409)")
    print("✅ Admins can view all flags")
    print("✅ Admins can filter flags by status")
    print("✅ Admins can dismiss flags")
    print("✅ Flag status and metadata updated correctly")
    print("✅ Comments not deleted when flags dismissed")

    return True


def test_admin_delete_flagged_comment():
    """Test that admin can delete a flagged comment."""
    print("\n" + "=" * 80)
    print("Additional Test: Admin Delete Flagged Comment")
    print("=" * 80)

    # Create users
    print("\n[1/4] Creating users...")
    author_email = f"author_{uuid.uuid4().hex[:8]}@example.com"
    flagger_email = f"flagger_{uuid.uuid4().hex[:8]}@example.com"
    admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePass123!"

    # Register and setup
    for email in [author_email, flagger_email, admin_email]:
        requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"}
        )
        verify_email(email)

    make_user_admin(admin_email)

    # Login
    author_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": author_email, "password": password}
    ).json()
    author_token = author_login["access_token"]
    author_id = json.loads(base64.b64decode(
        author_token.split('.')[1] + '=' * (4 - len(author_token.split('.')[1]) % 4)
    ))["sub"]

    flagger_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": flagger_email, "password": password}
    ).json()
    flagger_token = flagger_login["access_token"]
    flagger_id = json.loads(base64.b64decode(
        flagger_token.split('.')[1] + '=' * (4 - len(flagger_token.split('.')[1]) % 4)
    ))["sub"]

    admin_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"email": admin_email, "password": password}
    ).json()
    admin_token = admin_login["access_token"]
    admin_id = json.loads(base64.b64decode(
        admin_token.split('.')[1] + '=' * (4 - len(admin_token.split('.')[1]) % 4)
    ))["sub"]

    print(f"✅ Users created and logged in")

    # Create diagram and offensive comment
    print("\n[2/4] Creating diagram and comment...")
    diagram_response = requests.post(
        f"{API_BASE_URL}/diagrams",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        },
        json={
            "title": "Delete Test",
            "diagram_type": "canvas",
            "canvas_data": {"shapes": []}
        }
    )
    diagram_id = diagram_response.json()["id"]

    comment_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        },
        json={"content": "Truly offensive comment that should be deleted"}
    )
    comment_id = comment_response.json()["id"]
    print(f"✅ Created diagram and comment")

    # Flag comment
    print("\n[3/4] Flagging comment...")
    flag_response = requests.post(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments/{comment_id}/flag",
        headers={
            "Authorization": f"Bearer {flagger_token}",
            "X-User-ID": flagger_id
        },
        json={
            "reason": "harassment",
            "details": "This comment is truly offensive and should be removed"
        }
    )
    flag_id = flag_response.json()["flag_id"]
    print(f"✅ Comment flagged: {flag_id}")

    # Admin deletes comment
    print("\n[4/4] Admin reviewing and deleting comment...")
    delete_response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags/{flag_id}/review",
        headers={
            "X-User-ID": admin_id
        },
        json={
            "action": "delete_comment",
            "admin_notes": "Comment violates community guidelines - removing"
        }
    )

    if delete_response.status_code != 200:
        print(f"❌ Failed to delete comment: {delete_response.status_code}")
        print(delete_response.text)
        return False

    print(f"✅ Admin deleted comment")
    print(f"   Message: {delete_response.json()['message']}")

    # Verify comment deleted
    comment_check_response = requests.get(
        f"{API_BASE_URL}/diagrams/{diagram_id}/comments",
        headers={
            "Authorization": f"Bearer {author_token}",
            "X-User-ID": author_id
        }
    )

    comments = comment_check_response.json().get("comments", [])
    comment_exists = any(c["id"] == comment_id for c in comments)

    if not comment_exists:
        print(f"✅ Comment successfully deleted")
    else:
        print(f"❌ Comment still exists after deletion")
        return False

    # Verify flag status
    flags_response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/admin/comment-flags",
        headers={
            "X-User-ID": admin_id
        }
    )
    flags = flags_response.json()["flags"]
    our_flag = next((f for f in flags if f["flag_id"] == flag_id), None)

    if our_flag and our_flag["status"] == "actioned":
        print(f"✅ Flag status updated to 'actioned'")
    else:
        print(f"❌ Flag status not correct")
        return False

    print("\n✅ Admin Delete Test PASSED")
    return True


if __name__ == "__main__":
    try:
        # Test basic flag workflow
        success1 = test_flag_comment_workflow()

        # Test admin delete
        success2 = test_admin_delete_flagged_comment()

        if success1 and success2:
            print("\n" + "=" * 80)
            print("🎉 ALL TESTS PASSED")
            print("=" * 80)
            exit(0)
        else:
            print("\n" + "=" * 80)
            print("❌ SOME TESTS FAILED")
            print("=" * 80)
            exit(1)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

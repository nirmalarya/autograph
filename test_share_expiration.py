#!/usr/bin/env python3
"""Test Feature #137: Share diagram with expiration date."""

import requests
import json
from datetime import datetime, timedelta, timezone
import time

BASE_URL = "http://localhost:8082"
AUTH_URL = "http://localhost:8085"

def test_share_expiration():
    """Test share diagram with expiration date."""
    
    print("=" * 80)
    print("FEATURE #137: SHARE DIAGRAM WITH EXPIRATION DATE")
    print("=" * 80)
    
    # Step 1: Register and login
    print("\n1. Register and login user...")
    register_data = {
        "email": f"expiration_test_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "full_name": "Expiration Test User"
    }
    
    response = requests.post(f"{AUTH_URL}/register", json=register_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Registration failed: {response.status_code}")
        print(response.text)
        return False
    
    print("✅ User registered")
    
    # Login
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"]
    }
    
    response = requests.post(f"{AUTH_URL}/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(response.text)
        return False
    
    tokens = response.json()
    access_token = tokens["access_token"]
    
    # Decode JWT to get user_id
    import jwt
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    user_id = decoded["sub"]
    print(f"✅ User logged in (user_id: {user_id})")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-User-ID": user_id
    }
    
    # Step 2: Create a diagram
    print("\n2. Create diagram...")
    diagram_data = {
        "title": "Test Diagram for Expiration",
        "type": "canvas",
        "canvas_data": {"shapes": [], "version": 1},
        "note_content": "Test diagram for share expiration"
    }
    
    response = requests.post(f"{BASE_URL}/", json=diagram_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {response.status_code}")
        print(response.text)
        return False
    
    diagram = response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created (id: {diagram_id})")
    
    # Step 3: Create share link with 7-day expiration
    print("\n3. Create share link with 7-day expiration...")
    share_data = {
        "permission": "view",
        "is_public": True,
        "expires_in_days": 7
    }
    
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data,
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Share creation failed: {response.status_code}")
        print(response.text)
        return False
    
    share = response.json()
    share_token = share["token"]
    expires_at_str = share.get("expires_at")
    
    print(f"✅ Share link created")
    print(f"   Token: {share_token[:20]}...")
    print(f"   Expires at: {expires_at_str}")
    
    if not expires_at_str:
        print("❌ Expiration date not set!")
        return False
    
    # Parse expiration date
    expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    days_until_expiry = (expires_at - now).days
    
    print(f"   Days until expiry: {days_until_expiry}")
    
    if days_until_expiry < 6 or days_until_expiry > 7:
        print(f"❌ Expiration date incorrect! Expected ~7 days, got {days_until_expiry}")
        return False
    
    # Step 4: Verify link works within 7 days
    print("\n4. Verify link works within 7 days...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Share access failed: {response.status_code}")
        print(response.text)
        return False
    
    shared_diagram = response.json()
    print(f"✅ Share link works (diagram: {shared_diagram['title']})")
    
    # Step 5: Test expiration by creating an expired share
    print("\n5. Test expiration with past date...")
    print("   (Creating share that expired 1 day ago)")
    
    # We'll test this by directly manipulating the database
    # For now, let's create a share with 0 days expiration and wait a second
    share_data_expired = {
        "permission": "view",
        "is_public": True,
        "expires_in_days": 0  # Expires immediately (today)
    }
    
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data_expired,
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Expired share creation failed: {response.status_code}")
        print(response.text)
        return False
    
    expired_share = response.json()
    expired_token = expired_share["token"]
    
    print(f"✅ Created share with 0-day expiration")
    print(f"   Token: {expired_token[:20]}...")
    
    # Wait a moment and try to access
    print("\n6. Attempt to access expired share...")
    time.sleep(2)  # Wait 2 seconds
    
    # For a proper test, we need to manually set the expiration to the past
    # Let's use SQL to update the expiration date
    print("   Updating expiration to past date via database...")
    
    import psycopg2
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="autograph",
            user="autograph",
            password="autograph_dev_password"
        )
        
        cursor = conn.cursor()
        
        # Update the share to expire 1 day ago
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        cursor.execute(
            "UPDATE shares SET expires_at = %s WHERE token = %s",
            (past_date, expired_token)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Updated share expiration to: {past_date.isoformat()}")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")
        return False
    
    # Now try to access the expired share
    print("\n7. Access expired share link...")
    response = requests.get(f"{BASE_URL}/shared/{expired_token}")
    
    if response.status_code == 410:
        print(f"✅ Expired share correctly rejected with 410 Gone")
        error_detail = response.json().get("detail", "")
        print(f"   Error message: {error_detail}")
        
        if "expired" not in error_detail.lower():
            print(f"❌ Error message doesn't mention expiration!")
            return False
        
    elif response.status_code == 200:
        print(f"❌ Expired share was accepted! Should have been rejected.")
        return False
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        print(response.text)
        return False
    
    # Step 8: Verify non-expired share still works
    print("\n8. Verify non-expired share still works...")
    response = requests.get(f"{BASE_URL}/shared/{share_token}")
    
    if response.status_code != 200:
        print(f"❌ Non-expired share failed: {response.status_code}")
        print(response.text)
        return False
    
    print(f"✅ Non-expired share still works correctly")
    
    # Step 9: Test share without expiration
    print("\n9. Test share without expiration (should never expire)...")
    share_data_no_expiry = {
        "permission": "view",
        "is_public": True
        # No expires_in_days
    }
    
    response = requests.post(
        f"{BASE_URL}/{diagram_id}/share",
        json=share_data_no_expiry,
        headers=headers
    )
    
    if response.status_code not in [200, 201]:
        print(f"❌ Share without expiration failed: {response.status_code}")
        print(response.text)
        return False
    
    no_expiry_share = response.json()
    no_expiry_token = no_expiry_share["token"]
    no_expiry_expires_at = no_expiry_share.get("expires_at")
    
    print(f"✅ Share without expiration created")
    print(f"   Expires at: {no_expiry_expires_at}")
    
    if no_expiry_expires_at is not None:
        print(f"❌ Share should not have expiration date!")
        return False
    
    # Access it
    response = requests.get(f"{BASE_URL}/shared/{no_expiry_token}")
    
    if response.status_code != 200:
        print(f"❌ Share without expiration access failed: {response.status_code}")
        return False
    
    print(f"✅ Share without expiration works correctly")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED - Feature #137 Complete!")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_share_expiration()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

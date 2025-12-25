#!/usr/bin/env python3
"""
Feature #161: Diagram last activity timestamp

Tests that last_activity timestamp is updated on:
- Diagram creation
- Adding comments
- Editing canvas
- Another user viewing diagram
- Sorting diagrams by last activity
"""

import requests
import time
import json
import sys
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configuration
API_BASE_URL = "http://localhost:8080"  # API Gateway
AUTH_SERVICE_URL = "http://localhost:8085"  # Direct to auth service
DIAGRAM_SERVICE_URL = "http://localhost:8082"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log_step(step: str, status: str = "info"):
    """Log a test step."""
    color = Colors.BLUE if status == "info" else Colors.GREEN if status == "success" else Colors.RED
    print(f"{color}[{status.upper()}]{Colors.END} {step}")

def log_error(message: str):
    """Log an error message."""
    print(f"{Colors.RED}[ERROR]{Colors.END} {message}")

def log_success(message: str):
    """Log a success message."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.END} {message}")

def register_and_login(email: str, password: str, full_name: str) -> Optional[str]:
    """Register and login a user, return access token."""
    # Register
    register_data = {
        "email": email,
        "password": password,
        "username": email.split('@')[0]  # Use email prefix as username
    }

    response = requests.post(f"{AUTH_SERVICE_URL}/register", json=register_data)
    if response.status_code not in [200, 201]:
        # User might already exist, try login
        pass
    else:
        # Auto-verify email (for testing)
        user_data = response.json()
        user_id = user_data.get('user_id') or user_data.get('id')

        # Update user as verified in database
        try:
            conn = psycopg2.connect(
                host="localhost",
                database="autograph",
                user="autograph",
                password="autograph_dev_password",
                port=5432
            )
            cur = conn.cursor()
            cur.execute("UPDATE users SET is_verified = true WHERE id = %s", (user_id,))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            log_error(f"Failed to verify email: {e}")
            return None

    # Login
    login_data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{AUTH_SERVICE_URL}/login", json=login_data)
    if response.status_code != 200:
        log_error(f"Login failed: {response.text}")
        return None

    data = response.json()
    return data.get("access_token")

def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from token by decoding JWT."""
    import base64
    try:
        # JWT format: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None

        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
        return data.get('sub') or data.get('user_id')
    except:
        return None

def get_headers(token: str, user_id: Optional[str] = None) -> Dict[str, str]:
    """Get headers with auth token."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if user_id:
        headers["X-User-ID"] = user_id
    return headers

def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse datetime string."""
    if not dt_str:
        return None
    try:
        # Try with timezone
        if 'T' in dt_str:
            if dt_str.endswith('Z'):
                return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return datetime.fromisoformat(dt_str)
        return datetime.fromisoformat(dt_str)
    except:
        return None

def main():
    """Run all validation tests."""
    print("\n" + "="*80)
    print("Feature #161: Diagram last activity timestamp")
    print("="*80 + "\n")

    # Step 1: Register and login two users
    log_step("Step 1: Register and login two users")

    user1_email = f"lastactivity1_{int(time.time())}@example.com"
    user1_password = "SecurePass123!"
    user1_token = register_and_login(user1_email, user1_password, "Last Activity User 1")

    if not user1_token:
        log_error("Failed to register/login user 1")
        return False

    user2_email = f"lastactivity2_{int(time.time())}@example.com"
    user2_password = "SecurePass123!"
    user2_token = register_and_login(user2_email, user2_password, "Last Activity User 2")

    if not user2_token:
        log_error("Failed to register/login user 2")
        return False

    # Extract user IDs from tokens
    user1_id = get_user_id_from_token(user1_token)
    user2_id = get_user_id_from_token(user2_token)

    if not user1_id or not user2_id:
        log_error("Failed to extract user IDs from tokens")
        return False

    log_success(f"✅ Both users registered and logged in (User1: {user1_id}, User2: {user2_id})")

    # Step 2: User 1 creates a diagram
    log_step("Step 2: User 1 creates a diagram")

    diagram_data = {
        "title": "Last Activity Test Diagram",
        "file_type": "canvas",
        "canvas_data": {
            "nodes": [
                {"id": "node1", "type": "rectangle", "x": 100, "y": 100, "width": 100, "height": 50}
            ]
        }
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/",
        headers=get_headers(user1_token, user1_id),
        json=diagram_data
    )

    if response.status_code not in [200, 201]:
        log_error(f"Failed to create diagram: {response.text}")
        return False

    diagram = response.json()
    diagram_id = diagram["id"]
    initial_last_activity = parse_datetime(diagram.get("last_activity"))

    log_success(f"✅ Diagram created with ID: {diagram_id}")
    log_success(f"   Initial last_activity: {initial_last_activity}")

    if not initial_last_activity:
        log_error("❌ last_activity not set on creation")
        return False

    # Wait 2 seconds to ensure different timestamps
    time.sleep(2)

    # Step 3: User 1 adds a comment
    log_step("Step 3: User 1 adds a comment")

    comment_data = {
        "content": "This is a test comment to update last_activity"
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/comments",
        headers=get_headers(user1_token, user1_id),
        json=comment_data
    )

    if response.status_code not in [200, 201]:
        log_error(f"Failed to add comment: {response.text}")
        return False

    log_success(f"✅ Comment added")

    # Wait 1 second
    time.sleep(1)

    # Step 4: Verify last_activity updated after comment
    log_step("Step 4: Verify last_activity updated after comment")

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=get_headers(user1_token, user1_id)
    )

    if response.status_code != 200:
        log_error(f"Failed to get diagram: {response.text}")
        return False

    diagram = response.json()
    after_comment_last_activity = parse_datetime(diagram.get("last_activity"))

    log_success(f"   After comment last_activity: {after_comment_last_activity}")

    if not after_comment_last_activity or after_comment_last_activity <= initial_last_activity:
        log_error(f"❌ last_activity not updated after comment")
        log_error(f"   Initial: {initial_last_activity}")
        log_error(f"   After comment: {after_comment_last_activity}")
        return False

    log_success(f"✅ last_activity updated after comment")

    # Wait 2 seconds
    time.sleep(2)

    # Step 5: User 1 edits the canvas
    log_step("Step 5: User 1 edits the canvas")

    update_data = {
        "canvas_data": {
            "shapes": [
                {"id": "shape1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100},
                {"id": "shape2", "type": "circle", "x": 400, "y": 200, "radius": 50}
            ]
        }
    }

    response = requests.put(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=get_headers(user1_token, user1_id),
        json=update_data
    )

    if response.status_code != 200:
        log_error(f"Failed to update diagram: {response.text}")
        return False

    log_success(f"✅ Canvas edited")

    # Wait 1 second
    time.sleep(1)

    # Step 6: Verify last_activity updated after edit
    log_step("Step 6: Verify last_activity updated after edit")

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=get_headers(user1_token, user1_id)
    )

    if response.status_code != 200:
        log_error(f"Failed to get diagram: {response.text}")
        return False

    diagram = response.json()
    after_edit_last_activity = parse_datetime(diagram.get("last_activity"))

    log_success(f"   After edit last_activity: {after_edit_last_activity}")

    if not after_edit_last_activity or after_edit_last_activity <= after_comment_last_activity:
        log_error(f"❌ last_activity not updated after edit")
        log_error(f"   After comment: {after_comment_last_activity}")
        log_error(f"   After edit: {after_edit_last_activity}")
        return False

    log_success(f"✅ last_activity updated after edit")

    # Wait 2 seconds
    time.sleep(2)

    # Step 7: User 2 views the diagram (via share link or direct access)
    log_step("Step 7: User 2 views the diagram")

    # First, create a share link so user 2 can access
    share_data = {
        "permission": "view",
        "is_public": True
    }

    response = requests.post(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}/share",
        headers=get_headers(user1_token, user1_id),
        json=share_data
    )

    if response.status_code not in [200, 201]:
        log_error(f"Failed to create share link: {response.text}")
        return False

    share = response.json()
    share_token = share.get("token")

    log_success(f"✅ Share link created: {share_token}")

    # User 2 views via share link
    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/shared/{share_token}",
        headers=get_headers(user2_token, user2_id)
    )

    if response.status_code != 200:
        log_error(f"Failed to view diagram via share: {response.text}")
        return False

    log_success(f"✅ User 2 viewed diagram via share link")

    # Wait 1 second
    time.sleep(1)

    # Step 8: Verify last_activity updated after view
    log_step("Step 8: Verify last_activity updated after another user views")

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/{diagram_id}",
        headers=get_headers(user1_token, user1_id)
    )

    if response.status_code != 200:
        log_error(f"Failed to get diagram: {response.text}")
        return False

    diagram = response.json()
    after_view_last_activity = parse_datetime(diagram.get("last_activity"))

    log_success(f"   After view last_activity: {after_view_last_activity}")

    if not after_view_last_activity or after_view_last_activity <= after_edit_last_activity:
        log_error(f"❌ last_activity not updated after view")
        log_error(f"   After edit: {after_edit_last_activity}")
        log_error(f"   After view: {after_view_last_activity}")
        return False

    log_success(f"✅ last_activity updated after another user views")

    # Step 9: Create multiple diagrams with different last_activity times
    log_step("Step 9: Create multiple diagrams for sorting test")

    diagram_ids = [diagram_id]  # Include the first diagram

    for i in range(3):
        time.sleep(2)  # Ensure different timestamps

        test_diagram_data = {
            "title": f"Sort Test Diagram {i+1}",
            "file_type": "canvas",
            "canvas_data": {
                "shapes": [{"id": f"shape{i}", "type": "rectangle", "x": 100, "y": 100}]
            }
        }

        response = requests.post(
            f"{DIAGRAM_SERVICE_URL}/",
            headers=get_headers(user1_token, user1_id),
            json=test_diagram_data
        )

        if response.status_code in [200, 201]:
            new_diagram = response.json()
            diagram_ids.append(new_diagram["id"])
            log_success(f"✅ Created diagram {i+1}: {new_diagram['id']}")
        else:
            log_error(f"Failed to create test diagram {i+1}")

    # Step 10: Sort diagrams by last activity
    log_step("Step 10: Sort diagrams by last_activity (most recent first)")

    response = requests.get(
        f"{DIAGRAM_SERVICE_URL}/?sort_by=last_activity&sort_order=desc",
        headers=get_headers(user1_token, user1_id)
    )

    if response.status_code != 200:
        log_error(f"Failed to list diagrams: {response.text}")
        return False

    data = response.json()
    diagrams_list = data.get("diagrams", [])

    log_success(f"✅ Retrieved {len(diagrams_list)} diagrams")

    # Step 11: Verify most recently active diagrams are first
    log_step("Step 11: Verify diagrams are sorted by last_activity (descending)")

    last_activities = []
    for idx, diag in enumerate(diagrams_list[:5]):  # Check first 5
        last_act = parse_datetime(diag.get("last_activity"))
        last_activities.append(last_act)
        log_success(f"   Diagram {idx+1}: {diag['title'][:30]} - last_activity: {last_act}")

    # Verify descending order
    is_sorted = all(
        last_activities[i] >= last_activities[i+1]
        for i in range(len(last_activities)-1)
        if last_activities[i] and last_activities[i+1]
    )

    if not is_sorted:
        log_error("❌ Diagrams not sorted by last_activity in descending order")
        return False

    log_success(f"✅ Diagrams correctly sorted by last_activity (most recent first)")

    # All tests passed
    print("\n" + "="*80)
    log_success("✅ ALL TESTS PASSED - Feature #161 validated successfully!")
    print("="*80 + "\n")

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        log_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

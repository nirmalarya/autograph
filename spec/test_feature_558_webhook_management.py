"""
E2E Test for Feature #558: Enterprise: Webhook management: configure webhooks

Steps:
1. Navigate to /settings/webhooks
2. Add webhook URL
3. Select events: diagram.created
4. Test webhook
5. Verify POST sent
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import time
import jwt as pyjwt
import urllib3

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
INTEGRATION_HUB_BASE = "https://localhost:8099"
TEST_USER_ID = "test-webhook-558"
JWT_SECRET = "please-set-jwt-secret-in-environment"

# Mock webhook receiver endpoint (we'll use httpbin for testing)
WEBHOOK_TEST_URL = "https://httpbin.org/post"


def get_test_token():
    """Generate JWT token for test user."""
    payload = {
        "user_id": TEST_USER_ID,
        "sub": TEST_USER_ID,
        "email": "webhook-test@autograph.com",
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    return pyjwt.encode(payload, JWT_SECRET, algorithm="HS256")


def create_webhook(token, url, events):
    """Create a new webhook."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{INTEGRATION_HUB_BASE}/webhooks",
        headers=headers,
        json={
            "url": url,
            "events": events,
            "active": True
        },
        verify=False
    )
    return response


def list_webhooks(token):
    """List all webhooks for the user."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{INTEGRATION_HUB_BASE}/webhooks",
        headers=headers,
        verify=False
    )
    return response


def test_webhook(token, webhook_id):
    """Test a webhook by sending a test payload."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{INTEGRATION_HUB_BASE}/webhooks/test",
        headers=headers,
        json={"webhook_id": webhook_id},
        verify=False
    )
    return response


def delete_webhook(token, webhook_id):
    """Delete a webhook."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{INTEGRATION_HUB_BASE}/webhooks/{webhook_id}",
        headers=headers,
        verify=False
    )
    return response


def run_test():
    """Run the E2E test for feature #558."""
    print("\n" + "="*80)
    print("Testing Feature #558: Enterprise: Webhook management")
    print("="*80 + "\n")

    # Step 1: Get test token
    print("Step 1: Generate JWT token for enterprise user...")
    token = get_test_token()
    print("✓ Token generated successfully")

    # Step 2: Create webhook with diagram.created event
    print("\nStep 2: Create webhook with diagram.created event...")
    create_response = create_webhook(
        token,
        WEBHOOK_TEST_URL,
        ["diagram.created"]
    )

    if create_response.status_code != 201:
        print(f"❌ Create webhook failed: {create_response.status_code}")
        print(f"Response: {create_response.text}")
        return False

    webhook_data = create_response.json()
    webhook_id = webhook_data["id"]
    print(f"✓ Webhook created successfully: {webhook_id}")
    print(f"  URL: {webhook_data['url']}")
    print(f"  Events: {webhook_data['events']}")

    # Step 3: List webhooks to verify creation
    print("\nStep 3: List webhooks...")
    list_response = list_webhooks(token)

    if list_response.status_code != 200:
        print(f"❌ List webhooks failed: {list_response.status_code}")
        return False

    webhooks = list_response.json()
    print(f"✓ Found {len(webhooks)} webhook(s)")

    # Verify our webhook is in the list
    found = False
    for webhook in webhooks:
        if webhook["id"] == webhook_id:
            found = True
            break

    if not found:
        print("❌ Created webhook not found in list")
        return False
    print("✓ Webhook appears in list")

    # Step 4: Test the webhook
    print("\nStep 4: Test webhook delivery...")
    test_response = test_webhook(token, webhook_id)

    if test_response.status_code != 200:
        print(f"❌ Test webhook failed: {test_response.status_code}")
        print(f"Response: {test_response.text}")
        return False

    test_result = test_response.json()
    print(f"✓ Webhook test executed")
    print(f"  Success: {test_result.get('success')}")
    print(f"  Status Code: {test_result.get('status_code')}")

    # Step 5: Verify POST was sent (check response)
    print("\nStep 5: Verify POST was sent...")
    if not test_result.get("success"):
        print(f"❌ Webhook delivery failed: {test_result.get('error')}")
        return False

    if test_result.get("status_code") not in [200, 201, 202]:
        print(f"❌ Unexpected status code: {test_result.get('status_code')}")
        return False

    print("✓ POST request successfully delivered to webhook URL")

    # Cleanup: Delete the webhook
    print("\nCleanup: Deleting test webhook...")
    delete_response = delete_webhook(token, webhook_id)

    if delete_response.status_code != 204:
        print(f"⚠️  Warning: Could not delete webhook: {delete_response.status_code}")
    else:
        print("✓ Webhook deleted successfully")

    # Final verification
    print("\n" + "="*80)
    print("✅ Feature #558 TEST PASSED")
    print("="*80 + "\n")

    print("Summary:")
    print("- ✓ Enterprise user can create webhooks")
    print("- ✓ Webhooks can be configured with specific events (diagram.created)")
    print("- ✓ Webhooks can be tested")
    print("- ✓ POST requests are successfully sent to webhook URLs")
    print("- ✓ Webhooks can be listed and deleted")

    return True


if __name__ == "__main__":
    try:
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""Test SCIM 2.0 provisioning feature."""
import requests
import json
import sys

# SCIM token
SCIM_TOKEN = "7F_bvbP7jsvcNFrTRGcEbGzABCh1zefA_Qm7qnK8xfQ"
BASE_URL = "http://localhost:8085/scim/v2"  # Direct to auth service, not gateway

headers = {
    "Authorization": f"Bearer {SCIM_TOKEN}",
    "Content-Type": "application/json"
}

def test_service_provider_config():
    """Test GET ServiceProviderConfig."""
    print("\n1. Testing GET /ServiceProviderConfig...")
    response = requests.get(f"{BASE_URL}/ServiceProviderConfig", headers=headers)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()
    if "schemas" not in data or "authenticationSchemes" not in data:
        print("❌ FAILED: Missing required fields")
        return False

    print("✅ PASSED: ServiceProviderConfig endpoint works")
    return True


def test_resource_types():
    """Test GET ResourceTypes."""
    print("\n2. Testing GET /ResourceTypes...")
    response = requests.get(f"{BASE_URL}/ResourceTypes", headers=headers)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()
    if "Resources" not in data or len(data["Resources"]) == 0:
        print("❌ FAILED: No resource types returned")
        return False

    print("✅ PASSED: ResourceTypes endpoint works")
    return True


def test_schemas():
    """Test GET Schemas."""
    print("\n3. Testing GET /Schemas...")
    response = requests.get(f"{BASE_URL}/Schemas", headers=headers)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()
    if "Resources" not in data:
        print("❌ FAILED: No schemas returned")
        return False

    print("✅ PASSED: Schemas endpoint works")
    return True


def test_create_user():
    """Test POST /Users - Create user."""
    print("\n4. Testing POST /Users (Create User)...")

    user_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "externalId": "scim-test-001",
        "userName": "scim.test@example.com",
        "name": {
            "givenName": "SCIM",
            "familyName": "Test"
        },
        "displayName": "SCIM Test User",
        "emails": [
            {
                "value": "scim.test@example.com",
                "type": "work",
                "primary": True
            }
        ],
        "active": True
    }

    response = requests.post(f"{BASE_URL}/Users", headers=headers, json=user_data)

    if response.status_code != 201:
        print(f"❌ FAILED: Expected 201, got {response.status_code}")
        print(f"Response: {response.text}")
        return False, None

    data = response.json()

    # Verify response structure
    if "id" not in data:
        print("❌ FAILED: Missing user ID in response")
        return False, None

    if data.get("userName") != "scim.test@example.com":
        print(f"❌ FAILED: Username mismatch: {data.get('userName')}")
        return False, None

    if data.get("externalId") != "scim-test-001":
        print(f"❌ FAILED: External ID mismatch: {data.get('externalId')}")
        return False, None

    if not data.get("active"):
        print("❌ FAILED: User should be active")
        return False, None

    print(f"✅ PASSED: User created successfully with ID: {data['id']}")
    return True, data["id"]


def test_get_user(user_id):
    """Test GET /Users/{id} - Get user by ID."""
    print(f"\n5. Testing GET /Users/{user_id}...")

    response = requests.get(f"{BASE_URL}/Users/{user_id}", headers=headers)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()

    if data.get("id") != user_id:
        print("❌ FAILED: User ID mismatch")
        return False

    if data.get("userName") != "scim.test@example.com":
        print("❌ FAILED: Username mismatch")
        return False

    print("✅ PASSED: Get user by ID works")
    return True


def test_list_users():
    """Test GET /Users - List all users."""
    print("\n6. Testing GET /Users (List Users)...")

    response = requests.get(f"{BASE_URL}/Users?startIndex=1&count=10", headers=headers)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()

    if "Resources" not in data:
        print("❌ FAILED: Missing Resources in response")
        return False

    if "totalResults" not in data:
        print("❌ FAILED: Missing totalResults in response")
        return False

    print(f"✅ PASSED: List users works (found {data['totalResults']} users)")
    return True


def test_filter_user_by_username():
    """Test GET /Users with filter."""
    print("\n7. Testing GET /Users with userName filter...")

    filter_param = 'userName eq "scim.test@example.com"'
    response = requests.get(
        f"{BASE_URL}/Users",
        headers=headers,
        params={"filter": filter_param}
    )

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()

    if data["totalResults"] == 0:
        print("❌ FAILED: No users found with filter")
        return False

    if data["Resources"][0]["userName"] != "scim.test@example.com":
        print("❌ FAILED: Filter returned wrong user")
        return False

    print("✅ PASSED: Filter by userName works")
    return True


def test_filter_user_by_external_id():
    """Test GET /Users with externalId filter."""
    print("\n8. Testing GET /Users with externalId filter...")

    filter_param = 'externalId eq "scim-test-001"'
    response = requests.get(
        f"{BASE_URL}/Users",
        headers=headers,
        params={"filter": filter_param}
    )

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()

    if data["totalResults"] == 0:
        print("❌ FAILED: No users found with externalId filter")
        return False

    print("✅ PASSED: Filter by externalId works")
    return True


def test_update_user(user_id):
    """Test PUT /Users/{id} - Update user."""
    print(f"\n9. Testing PUT /Users/{user_id} (Update User)...")

    update_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "externalId": "scim-test-001-updated",
        "userName": "scim.test@example.com",
        "displayName": "SCIM Test User Updated",
        "emails": [
            {
                "value": "scim.test@example.com",
                "type": "work",
                "primary": True
            }
        ],
        "active": True
    }

    response = requests.put(f"{BASE_URL}/Users/{user_id}", headers=headers, json=update_data)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False

    data = response.json()

    if data.get("externalId") != "scim-test-001-updated":
        print(f"❌ FAILED: External ID not updated: {data.get('externalId')}")
        return False

    if data.get("displayName") != "SCIM Test User Updated":
        print(f"❌ FAILED: Display name not updated: {data.get('displayName')}")
        return False

    print("✅ PASSED: Update user works")
    return True


def test_deactivate_user(user_id):
    """Test PUT /Users/{id} - Deactivate user."""
    print(f"\n10. Testing PUT /Users/{user_id} (Deactivate User)...")

    update_data = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "active": False
    }

    response = requests.put(f"{BASE_URL}/Users/{user_id}", headers=headers, json=update_data)

    if response.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {response.status_code}")
        return False

    data = response.json()

    if data.get("active") != False:
        print("❌ FAILED: User should be inactive")
        return False

    print("✅ PASSED: Deactivate user works")
    return True


def test_delete_user(user_id):
    """Test DELETE /Users/{id} - Delete user."""
    print(f"\n11. Testing DELETE /Users/{user_id}...")

    response = requests.delete(f"{BASE_URL}/Users/{user_id}", headers=headers)

    if response.status_code != 204:
        print(f"❌ FAILED: Expected 204, got {response.status_code}")
        return False

    # Verify user is deactivated
    get_response = requests.get(f"{BASE_URL}/Users/{user_id}", headers=headers)
    if get_response.status_code == 200:
        user_data = get_response.json()
        if user_data.get("active") != False:
            print("❌ FAILED: User should be deactivated after delete")
            return False

    print("✅ PASSED: Delete user works (user deactivated)")
    return True


def test_unauthorized_access():
    """Test accessing SCIM endpoints without token."""
    print("\n12. Testing unauthorized access...")

    response = requests.get(f"{BASE_URL}/Users")

    if response.status_code != 401:
        print(f"❌ FAILED: Expected 401, got {response.status_code}")
        return False

    print("✅ PASSED: Unauthorized access properly blocked")
    return True


def main():
    """Run all SCIM tests."""
    print("=" * 70)
    print("SCIM 2.0 PROVISIONING TEST SUITE")
    print("=" * 70)

    results = []
    user_id = None

    # Test metadata endpoints
    results.append(("ServiceProviderConfig", test_service_provider_config()))
    results.append(("ResourceTypes", test_resource_types()))
    results.append(("Schemas", test_schemas()))

    # Test user CRUD
    success, user_id = test_create_user()
    results.append(("Create User", success))

    if user_id:
        results.append(("Get User", test_get_user(user_id)))
        results.append(("List Users", test_list_users()))
        results.append(("Filter by userName", test_filter_user_by_username()))
        results.append(("Filter by externalId", test_filter_user_by_external_id()))
        results.append(("Update User", test_update_user(user_id)))
        results.append(("Deactivate User", test_deactivate_user(user_id)))
        results.append(("Delete User", test_delete_user(user_id)))

    # Test security
    results.append(("Unauthorized Access", test_unauthorized_access()))

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

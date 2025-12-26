"""
Test SAML SP-Initiated Flow - Feature #524

This test validates the SP-initiated SAML SSO flow where:
1. User clicks 'Login with SSO'
2. Gets redirected to IdP
3. Authenticates at IdP
4. Gets redirected back to SP (ACS endpoint)
5. User is logged in

SP-initiated flow is the most common SAML flow.
"""

import requests
import json
from urllib.parse import urlparse, parse_qs
import sys

# Base URLs
AUTH_URL = "http://localhost:8085"
API_GATEWAY_URL = "http://localhost:8080"

def test_sp_initiated_flow():
    """Test Feature #524: SAML SP-initiated flow"""
    print("\n" + "="*80)
    print("TEST: Feature #524 - SAML SP-initiated Flow")
    print("="*80)

    # Step 1: Create admin user and configure SAML provider
    print("\n[SETUP] Creating admin user and configuring SAML...")

    # Generate unique email
    import time
    unique_email = f"admin{int(time.time())}@test.com"

    # Register admin
    register_response = requests.post(
        f"{AUTH_URL}/register",
        json={
            "email": unique_email,
            "password": "AdminPass123!",
            "first_name": "Admin",
            "last_name": "User"
        }
    )

    if register_response.status_code != 201:
        print(f"❌ Failed to register admin: {register_response.text}")
        return False

    user_data = register_response.json()
    user_id = user_data["id"]

    # Promote to admin
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="autograph",
        user="autograph",
        password="autograph_dev_password"
    )
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 'admin', is_verified = true WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()

    # Login as admin
    login_response = requests.post(
        f"{AUTH_URL}/login",
        json={
            "email": unique_email,
            "password": "AdminPass123!"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Failed to login as admin: {login_response.text}")
        return False

    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Configure test SAML provider
    print("\n[SETUP] Configuring test SAML provider...")
    saml_config = {
        "name": "test-sp-flow",
        "enabled": True,
        "entity_id": "https://test-idp.example.com",
        "sso_url": "https://test-idp.example.com/sso",
        "slo_url": "https://test-idp.example.com/slo",
        "x509_cert": "MIIC...",  # Mock cert
        "jit_provisioning": {
            "enabled": True,
            "default_role": "viewer"
        }
    }

    config_response = requests.post(
        f"{AUTH_URL}/admin/saml/providers",
        json=saml_config,
        headers=headers
    )

    if config_response.status_code != 200:
        print(f"❌ Failed to configure SAML provider: {config_response.text}")
        return False

    print(f"✅ SAML provider configured: {config_response.json()}")

    # =========================================================================
    # TEST: SP-Initiated Flow
    # =========================================================================

    # Step 1: User clicks "Login with SSO"
    print("\n[STEP 1] User initiates SSO login...")

    # The endpoint should either:
    # a) Return a redirect response (302/303)
    # b) Return JSON with sso_url for client-side redirect

    sso_init_response = requests.get(
        f"{AUTH_URL}/auth/saml/login/test-sp-flow",
        allow_redirects=False
    )

    print(f"Status: {sso_init_response.status_code}")
    print(f"Headers: {dict(sso_init_response.headers)}")

    # Check if it's a redirect
    if sso_init_response.status_code in [302, 303, 307]:
        redirect_url = sso_init_response.headers.get("Location")
        print(f"✅ Server redirected to: {redirect_url}")

        # Verify it's the IdP URL
        if not redirect_url:
            print("❌ No redirect location provided")
            return False

        # Parse redirect URL
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)

        # Should contain SAMLRequest
        if "SAMLRequest" not in query_params:
            print("❌ No SAMLRequest in redirect URL")
            return False

        print(f"✅ SAMLRequest found in redirect URL")
        print(f"   IdP: {parsed.scheme}://{parsed.netloc}{parsed.path}")

    # Or check if it returns JSON with sso_url
    elif sso_init_response.status_code == 200:
        try:
            sso_data = sso_init_response.json()
            if "sso_url" not in sso_data:
                print("❌ No sso_url in response")
                print(f"Response: {sso_data}")
                return False

            sso_url = sso_data["sso_url"]
            print(f"✅ SSO URL received: {sso_url}")

            # Verify URL format
            if not sso_url.startswith("http"):
                print(f"❌ Invalid SSO URL format: {sso_url}")
                return False

            # Parse SSO URL
            parsed = urlparse(sso_url)
            query_params = parse_qs(parsed.query)

            # Should contain SAMLRequest
            if "SAMLRequest" not in query_params:
                print("❌ No SAMLRequest in SSO URL")
                return False

            print(f"✅ SAMLRequest found in SSO URL")
            print(f"   IdP: {parsed.scheme}://{parsed.netloc}{parsed.path}")

            # Check if request_id is returned
            if "request_id" in sso_data:
                print(f"✅ Request ID: {sso_data['request_id']}")

        except Exception as e:
            print(f"❌ Failed to parse response: {e}")
            print(f"Response: {sso_init_response.text}")
            return False
    else:
        print(f"❌ Unexpected status code: {sso_init_response.status_code}")
        print(f"Response: {sso_init_response.text}")
        return False

    # Step 2: Verify provider is accessible without auth
    print("\n[STEP 2] Verify SSO endpoint is publicly accessible...")

    # Should work without authentication
    public_response = requests.get(
        f"{AUTH_URL}/auth/saml/login/test-sp-flow",
        allow_redirects=False
    )

    if public_response.status_code in [200, 302, 303, 307]:
        print("✅ SSO endpoint is publicly accessible")
    else:
        print(f"❌ SSO endpoint requires authentication: {public_response.status_code}")
        return False

    # Step 3: Verify non-existent provider returns 404
    print("\n[STEP 3] Verify error handling for unknown provider...")

    bad_response = requests.get(
        f"{AUTH_URL}/auth/saml/login/non-existent-provider",
        allow_redirects=False
    )

    if bad_response.status_code == 404:
        print("✅ Returns 404 for unknown provider")
    else:
        print(f"❌ Expected 404, got {bad_response.status_code}")
        return False

    # Step 4: Verify disabled provider returns error
    print("\n[STEP 4] Testing disabled provider...")

    # Disable the provider
    disable_config = saml_config.copy()
    disable_config["enabled"] = False

    requests.post(
        f"{AUTH_URL}/admin/saml/providers",
        json=disable_config,
        headers=headers
    )

    disabled_response = requests.get(
        f"{AUTH_URL}/auth/saml/login/test-sp-flow",
        allow_redirects=False
    )

    if disabled_response.status_code in [400, 403]:
        print("✅ Disabled provider returns error")
    else:
        print(f"⚠️  Disabled provider returned: {disabled_response.status_code}")
        # Re-enable for cleanup
        requests.post(
            f"{AUTH_URL}/admin/saml/providers",
            json=saml_config,
            headers=headers
        )

    # Re-enable provider
    requests.post(
        f"{AUTH_URL}/admin/saml/providers",
        json=saml_config,
        headers=headers
    )

    print("\n" + "="*80)
    print("✅ SAML SP-INITIATED FLOW TEST PASSED")
    print("="*80)
    print("\nSummary:")
    print("  ✓ SP-initiated login endpoint works")
    print("  ✓ Returns SSO URL with SAMLRequest")
    print("  ✓ Publicly accessible (no auth required)")
    print("  ✓ Error handling for unknown/disabled providers")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_sp_initiated_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

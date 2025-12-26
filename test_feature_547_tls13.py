#!/usr/bin/env python3
"""Test Feature #547: Encryption in transit - TLS 1.3"""
import ssl
import socket
import sys
from urllib.parse import urlparse

def test_tls_version(host, port, min_version, max_version=None):
    """Test TLS connection with specific version."""
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.minimum_version = min_version
        if max_version:
            context.maximum_version = max_version

        with socket.create_connection((host, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                version = ssock.version()
                cipher = ssock.cipher()
                print(f"✓ Connected with {version}, Cipher: {cipher[0]}")
                return True, version
    except ssl.SSLError as e:
        print(f"✗ SSL Error: {e}")
        return False, None
    except Exception as e:
        print(f"✗ Connection Error: {e}")
        return False, None

def main():
    print("=" * 80)
    print("Feature #547: Encryption in Transit - TLS 1.3")
    print("=" * 80)

    # Services to test
    services = [
        ("auth-service", "localhost", 8085),
        ("api-gateway", "localhost", 8080),
        ("diagram-service", "localhost", 8082),
        ("collaboration-service", "localhost", 8083),
        ("ai-service", "localhost", 8084),
    ]

    all_passed = True

    for service_name, host, port in services:
        print(f"\n📝 Testing {service_name} on {host}:{port}")
        print("-" * 80)

        # Test 1: TLS 1.3 should work
        print("\n1. Testing TLS 1.3 connection (SHOULD WORK):")
        success, version = test_tls_version(host, port, ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3)
        if success and version == "TLSv1.3":
            print(f"✅ PASS: {service_name} accepts TLS 1.3")
        else:
            print(f"❌ FAIL: {service_name} does not accept TLS 1.3")
            all_passed = False

        # Test 2: TLS 1.2 should be rejected
        print("\n2. Testing TLS 1.2 connection (SHOULD BE REJECTED):")
        success, version = test_tls_version(host, port, ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2)
        if not success:
            print(f"✅ PASS: {service_name} correctly rejects TLS 1.2")
        else:
            print(f"❌ FAIL: {service_name} incorrectly accepts TLS 1.2 (should only accept TLS 1.3)")
            all_passed = False

        # Test 3: TLS 1.1 should be rejected
        print("\n3. Testing TLS 1.1 connection (SHOULD BE REJECTED):")
        success, version = test_tls_version(host, port, ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1)
        if not success:
            print(f"✅ PASS: {service_name} correctly rejects TLS 1.1")
        else:
            print(f"❌ FAIL: {service_name} incorrectly accepts TLS 1.1 (should only accept TLS 1.3)")
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("✅ ALL TESTS PASSED - TLS 1.3 ONLY ENCRYPTION IN TRANSIT VERIFIED")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())

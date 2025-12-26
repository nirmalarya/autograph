#!/usr/bin/env python3
"""
Feature #480: Version history: Background compression: gzip old versions

Test Steps:
1. Create 50 versions
2. Wait for compression job
3. Verify old versions compressed
4. Verify storage space reduced
5. Verify decompression on access
"""

import requests
import time
import json
import base64
from datetime import datetime, timedelta

API_BASE = "http://localhost:8080"
AUTH_SERVICE = "http://localhost:8085"
DIAGRAM_SERVICE = "http://localhost:8082"

def test_feature_480_background_compression():
    """Test background compression of old diagram versions."""

    print("\n" + "="*60)
    print("Feature #480: Background Compression of Old Versions")
    print("="*60)

    # Step 1: Login with pre-created test user
    print("\n[1] Logging in with test user...")
    email = "compress480@test.com"
    password = "SecurePass123!"

    # Login
    login_response = requests.post(f"{AUTH_SERVICE}/login", json={
        "email": email,
        "password": password
    })

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False

    login_data = login_response.json()
    token = login_data["access_token"]

    # Decode JWT to get user ID
    payload = token.split('.')[1]
    # Add padding if needed
    payload += '=' * (4 - len(payload) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload))
    user_id = decoded["sub"]

    headers = {
        "Authorization": f"Bearer {token}",
        "X-User-ID": user_id
    }
    print(f"✅ User logged in: {email} (ID: {user_id})")

    # Step 2: Create a diagram (use diagram service directly)
    print("\n[2] Creating diagram...")
    diagram_response = requests.post(
        f"{DIAGRAM_SERVICE}/",
        headers=headers,
        json={
            "title": "Compression Test Diagram",
            "description": "Testing background compression",
            "diagram_type": "note"
        }
    )

    if diagram_response.status_code not in [200, 201]:
        print(f"❌ Diagram creation failed: {diagram_response.status_code}")
        return False

    diagram = diagram_response.json()
    diagram_id = diagram["id"]
    print(f"✅ Diagram created: {diagram_id}")

    # Step 3: Create 50 versions
    print("\n[3] Creating 50 versions (this will take a moment)...")
    version_ids = []

    for i in range(50):
        content = {
            "note_content": f"Version {i+1} content - " + ("x" * 1000),  # Make it substantial
            "diagram_type": "note"
        }

        response = requests.put(
            f"{DIAGRAM_SERVICE}/{diagram_id}",
            headers=headers,
            json=content
        )

        if response.status_code == 200:
            if (i + 1) % 10 == 0:
                print(f"  Created {i+1} versions...")
        else:
            print(f"❌ Failed to create version {i+1}: {response.status_code}")
            return False

        time.sleep(0.1)  # Small delay to avoid rate limiting

    print(f"✅ Created 50 versions successfully")

    # Step 4: Get version list before compression
    print("\n[4] Getting version list before compression...")
    versions_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions",
        headers=headers
    )

    if versions_response.status_code != 200:
        print(f"❌ Failed to get versions: {versions_response.status_code}")
        return False

    versions_data = versions_response.json()
    # Handle both list and paginated responses
    if isinstance(versions_data, dict) and "versions" in versions_data:
        versions_before = versions_data["versions"]
    else:
        versions_before = versions_data
    total_versions = len(versions_before)
    print(f"✅ Total versions: {total_versions}")

    # Step 5: Get compression stats before
    print("\n[5] Getting compression stats before compression...")
    stats_before_response = requests.get(
        f"{DIAGRAM_SERVICE}/versions/compression/stats",
        headers=headers
    )

    if stats_before_response.status_code != 200:
        print(f"❌ Failed to get stats: {stats_before_response.status_code}")
        return False

    stats_before = stats_before_response.json()
    print(f"  Compressed versions before: {stats_before.get('compressed_versions', 0)}")
    print(f"  Uncompressed versions before: {stats_before.get('uncompressed_versions', 0)}")

    # Step 6: Trigger background compression (compress versions older than 0 days = all versions)
    print("\n[6] Triggering background compression job...")
    print("  (Using min_age_days=0 to compress all versions immediately)")

    compress_response = requests.post(
        f"{DIAGRAM_SERVICE}/versions/compress/all?min_age_days=0&limit=100",
        headers=headers
    )

    if compress_response.status_code != 200:
        print(f"❌ Compression job failed: {compress_response.status_code}")
        print(compress_response.text)
        return False

    compress_result = compress_response.json()
    print(f"✅ Compression job completed:")
    print(f"  Versions found: {compress_result.get('versions_found', 0)}")
    print(f"  Versions compressed: {compress_result.get('versions_compressed', 0)}")
    print(f"  Total savings: {compress_result.get('total_savings_mb', 0)} MB")
    print(f"  Average compression ratio: {compress_result.get('avg_compression_ratio', 0):.2f}")

    # Step 7: Verify versions are compressed
    print("\n[7] Verifying versions are compressed...")
    stats_after_response = requests.get(
        f"{DIAGRAM_SERVICE}/versions/compression/stats",
        headers=headers
    )

    if stats_after_response.status_code != 200:
        print(f"❌ Failed to get stats after compression: {stats_after_response.status_code}")
        return False

    stats_after = stats_after_response.json()
    compressed_count = stats_after.get('compressed_versions', 0)

    print(f"  Compressed versions after: {compressed_count}")
    print(f"  Uncompressed versions after: {stats_after.get('uncompressed_versions', 0)}")

    if compressed_count == 0:
        print(f"❌ No versions were compressed!")
        return False

    print(f"✅ Versions successfully compressed")

    # Step 8: Verify storage space reduced
    print("\n[8] Verifying storage space reduced...")
    total_savings = stats_after.get('total_savings_bytes', 0)
    savings_mb = stats_after.get('total_savings_mb', 0)

    if total_savings > 0:
        print(f"✅ Storage space reduced by {savings_mb} MB ({total_savings} bytes)")
        compression_ratio = stats_after.get('avg_compression_ratio', 1.0)
        savings_percent = (1 - compression_ratio) * 100 if compression_ratio else 0
        print(f"  Average compression ratio: {compression_ratio:.2f}")
        print(f"  Average savings: {savings_percent:.1f}%")
    else:
        print(f"❌ No storage space saved!")
        return False

    # Step 9: Verify decompression on access
    print("\n[9] Verifying decompression works on access...")

    # Get a specific version (should decompress automatically)
    version_to_test = versions_before[10] if len(versions_before) > 10 else versions_before[0]
    version_id = version_to_test["id"]

    version_response = requests.get(
        f"{DIAGRAM_SERVICE}/{diagram_id}/versions/{version_id}",
        headers=headers
    )

    if version_response.status_code != 200:
        print(f"❌ Failed to get version: {version_response.status_code}")
        return False

    version_data = version_response.json()

    # Check if content is accessible
    if "note_content" in version_data and version_data["note_content"]:
        print(f"✅ Version content decompressed successfully")
        print(f"  Version {version_data.get('version_number')} has {len(version_data['note_content'])} characters")

        # Check if version shows compression info
        if version_data.get("is_compressed"):
            print(f"  Compression info:")
            comp_info = version_data.get("compression_info", {})
            print(f"    Original size: {comp_info.get('original_size', 0)} bytes")
            print(f"    Compressed size: {comp_info.get('compressed_size', 0)} bytes")
            print(f"    Savings: {comp_info.get('savings_percent', 0)}%")
    else:
        print(f"❌ Version content not accessible!")
        return False

    # Step 10: Summary
    print("\n" + "="*60)
    print("FEATURE #480 TEST SUMMARY")
    print("="*60)
    print(f"✅ Created 50 versions")
    print(f"✅ Triggered background compression job")
    print(f"✅ Verified {compressed_count} versions compressed")
    print(f"✅ Verified storage reduced by {savings_mb} MB")
    print(f"✅ Verified decompression works on access")
    print("="*60)
    print("✅ ALL TESTS PASSED - Feature #480 working correctly!")
    print("="*60)

    return True

if __name__ == "__main__":
    try:
        success = test_feature_480_background_compression()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

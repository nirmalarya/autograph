#!/usr/bin/env python3
"""Test markdown export feature #498"""
import requests
import sys

EXPORT_SERVICE_URL = "http://localhost:8097"

# Test markdown export
payload = {
    "diagram_id": "test-md-001",
    "canvas_data": {"shapes": []},
    "format": "md",
    "width": 1920,
    "height": 1080,
    "background": "white",
    "quality": "high",
    "scale": 1.0
}

try:
    response = requests.post(f"{EXPORT_SERVICE_URL}/export/markdown", json=payload)

    if response.status_code == 200:
        md_content = response.text
        print("✅ Markdown export successful")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   File size: {len(md_content)} bytes")
        print(f"   Content-Disposition: {response.headers.get('content-disposition')}")

        # Check markdown structure
        checks = {
            "YAML front matter": md_content.startswith("---"),
            "Diagram heading": "# test-md-001" in md_content,
            "Embedded image": "data:image/png;base64," in md_content,
            "Metadata section": "## Metadata" in md_content,
            "JSON metadata": '"diagram_id"' in md_content
        }

        print("\n   Markdown Structure Checks:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"     {status} {check}")

        # Save to file
        with open('/tmp/test_diagram.md', 'w') as f:
            f.write(md_content)
        print(f"\n   Saved to: /tmp/test_diagram.md")

        # Show first 500 chars
        print(f"\n   Preview (first 500 chars):")
        print("   " + "="*60)
        for line in md_content[:500].split('\n'):
            print(f"   {line}")
        print("   " + "="*60)

        if all(checks.values()):
            print("\n✅ Feature #498 PASSING - All checks passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some checks failed")
            sys.exit(1)
    else:
        print(f"❌ Export failed with status {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

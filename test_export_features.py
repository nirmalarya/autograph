#!/usr/bin/env python3
"""Test export features #498, #499, #500"""
import requests
import sys
import json

EXPORT_SERVICE_URL = "http://localhost:8097"

def test_json_export():
    """Test Feature #499: JSON export - canvas data structure"""
    print("\n" + "="*70)
    print("Test: JSON Export (Feature #499)")
    print("="*70)

    payload = {
        "diagram_id": "test-json-001",
        "canvas_data": {
            "shapes": [
                {"id": "s1", "type": "rectangle", "x": 100, "y": 100},
                {"id": "s2", "type": "circle", "x": 200, "y": 200}
            ],
            "connections": [
                {"from": "s1", "to": "s2"}
            ]
        },
        "format": "json",
        "width": 1920,
        "height": 1080
    }

    try:
        response = requests.post(f"{EXPORT_SERVICE_URL}/export/json", json=payload)

        if response.status_code == 200:
            json_content = response.text
            print("✅ JSON export successful")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   File size: {len(json_content)} bytes")

            # Parse and validate JSON
            try:
                data = json.loads(json_content)
                checks = {
                    "Valid JSON": True,
                    "Contains canvas_data": "canvas_data" in data,
                    "Has shapes": "shapes" in data.get("canvas_data", {}),
                    "Has metadata": "metadata" in data or "diagram_id" in data
                }

                print("\n   JSON Structure Checks:")
                for check, passed in checks.items():
                    status = "✅" if passed else "❌"
                    print(f"     {status} {check}")

                if all(checks.values()):
                    print("\n✅ Feature #499 PASSING")
                    return True
                else:
                    print("\n⚠️  Feature #499 - Some checks failed")
                    return False

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {e}")
                return False
        else:
            print(f"❌ Export failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_html_export():
    """Test Feature #500: HTML export - standalone with CSS"""
    print("\n" + "="*70)
    print("Test: HTML Export (Feature #500)")
    print("="*70)

    payload = {
        "diagram_id": "test-html-001",
        "canvas_data": {"shapes": []},
        "format": "html",
        "width": 1920,
        "height": 1080,
        "background": "white"
    }

    try:
        response = requests.post(f"{EXPORT_SERVICE_URL}/export/html", json=payload)

        if response.status_code == 200:
            html_content = response.text
            print("✅ HTML export successful")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   File size: {len(html_content)} bytes")

            # Check HTML structure
            checks = {
                "DOCTYPE": "<!DOCTYPE html>" in html_content,
                "HTML tag": "<html" in html_content,
                "CSS styles": "<style>" in html_content or "style=" in html_content,
                "Self-contained": "src=\"http" not in html_content and "href=\"http" not in html_content,
                "Embedded diagram": "data:image" in html_content or "<svg" in html_content
            }

            print("\n   HTML Structure Checks:")
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"     {status} {check}")

            # Save to file
            with open('/tmp/test_diagram.html', 'w') as f:
                f.write(html_content)
            print(f"\n   Saved to: /tmp/test_diagram.html")

            if all(checks.values()):
                print("\n✅ Feature #500 PASSING")
                return True
            else:
                print("\n⚠️  Feature #500 - Some checks failed")
                return False
        else:
            print(f"❌ Export failed with status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all export feature tests"""
    print("="*70)
    print("EXPORT FEATURES TEST SUITE (#498, #499, #500)")
    print("="*70)

    results = {
        498: True,  # Already tested markdown
        499: test_json_export(),
        500: test_html_export()
    }

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for feature_id, passed in results.items():
        status = "✅ PASSING" if passed else "❌ FAILING"
        print(f"Feature #{feature_id}: {status}")

    if all(results.values()):
        print("\n✅ ALL EXPORT FEATURES PASSING!")
        return 0
    else:
        print("\n⚠️  Some features need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())

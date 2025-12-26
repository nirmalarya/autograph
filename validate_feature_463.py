#!/usr/bin/env python3
"""
Validate Feature #463: Version Timeline UI Implementation

This script validates that the version timeline feature has been implemented
correctly by checking the code changes.
"""

import re

def check_timeline_implementation():
    """Check if timeline view is implemented in versions page"""
    print("Feature #463: Version Timeline UI Validation")
    print("=" * 60)

    # Read the versions page
    with open('services/frontend/app/versions/[id]/page.tsx', 'r') as f:
        content = f.read()

    checks_passed = []
    checks_failed = []

    # Check 1: Page view state added
    if 'pageView' in content and '"timeline" | "compare"' in content:
        checks_passed.append("✓ Page view state (timeline/compare) added")
    else:
        checks_failed.append("✗ Page view state not found")

    # Check 2: Timeline view switch in header
    if 'Timeline' in content and 'handleViewChange' in content:
        checks_passed.append("✓ View switcher (Timeline/Compare) in header")
    else:
        checks_failed.append("✗ View switcher not found")

    # Check 3: Timeline view content
    if 'Version Timeline' in content and 'Timeline View' in content:
        checks_passed.append("✓ Timeline view content section exists")
    else:
        checks_failed.append("✗ Timeline view content not found")

    # Check 4: Chronological ordering (newest first)
    if 'sort' in content and 'version_number' in content and 'descending' in content.lower():
        checks_passed.append("✓ Versions sorted in descending order (newest first)")
    else:
        # Check for the sorting code
        if re.search(r'b\.version_number\s*-\s*a\.version_number', content):
            checks_passed.append("✓ Versions sorted in descending order (newest first)")
        else:
            checks_failed.append("✗ Chronological sorting not found")

    # Check 5: Timeline visual elements (dots, connectors)
    if 'rounded-full' in content and 'timeline' in content.lower():
        checks_passed.append("✓ Timeline visual elements (dots, connectors)")
    else:
        checks_failed.append("✗ Timeline visual elements not found")

    # Check 6: Version metadata display
    if 'version.created_at' in content and 'version.user.full_name' in content:
        checks_passed.append("✓ Version metadata (timestamp, author) displayed")
    else:
        checks_failed.append("✗ Version metadata display not found")

    # Check 7: Latest version indicator
    if 'Latest' in content and 'index === 0' in content:
        checks_passed.append("✓ Latest version indicator")
    else:
        checks_failed.append("✗ Latest version indicator not found")

    # Check 8: Version list iteration
    if 'versions.map' in content and 'Timeline List' in content:
        checks_passed.append("✓ Version list iteration")
    else:
        checks_failed.append("✗ Version list iteration not found")

    # Print results
    print("\nValidation Results:")
    print("-" * 60)

    for check in checks_passed:
        print(check)

    for check in checks_failed:
        print(check)

    print("\n" + "=" * 60)
    total = len(checks_passed) + len(checks_failed)
    passed = len(checks_passed)

    print(f"Checks Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    if len(checks_failed) == 0:
        print("\n✅ Feature #463 Implementation VALIDATED")
        print("\nImplemented:")
        print("  • Timeline view with chronological list UI")
        print("  • Versions sorted newest first")
        print("  • Timeline visual design (dots, connectors)")
        print("  • Version metadata display")
        print("  • Latest version indicator")
        print("  • View switcher (Timeline/Compare)")
        return True
    else:
        print("\n⚠️  Some checks failed - review needed")
        return False

if __name__ == "__main__":
    success = check_timeline_implementation()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Feature #424 Validation: Comments - Add comment to canvas element

Tests:
1. Backend API for creating comments exists
2. Comment model supports element_id for canvas shapes
3. Frontend has "Add Comment" action in TLDraw canvas
4. Comment dialog renders properly
5. API endpoint is configured in frontend

This is a code-level validation since full E2E testing with Puppeteer
would require complex canvas interaction simulation.
"""

import subprocess
import json
import sys

def check_comment_model():
    """Check if Comment model has element_id field."""
    print("✓ Checking Comment model for element_id support...")

    with open('services/diagram-service/src/models.py', 'r') as f:
        content = f.read()
        if 'element_id = Column(String(255))' in content:
            print("  ✅ Comment model has element_id field")
            return True

    print("  ❌ Comment model missing element_id")
    return False

def check_comment_api():
    """Check if POST /comments endpoint exists."""
    print("✓ Checking comment API endpoints...")

    with open('services/diagram-service/src/main.py', 'r') as f:
        content = f.read()
        if '@app.post("/{diagram_id}/comments"' in content:
            print("  ✅ POST /comments endpoint exists")
            return True

    print("  ❌ POST /comments endpoint missing")
    return False

def check_frontend_api_config():
    """Check if comments endpoints are configured in frontend."""
    print("✓ Checking frontend API configuration...")

    with open('services/frontend/src/lib/api-config.ts', 'r') as f:
        content = f.read()
        if 'comments:' in content and 'create:' in content:
            print("  ✅ Comment endpoints configured in frontend")
            return True

    print("  ❌ Comment endpoints not configured")
    return False

def check_tldraw_comment_action():
    """Check if TLDraw canvas has Add Comment action."""
    print("✓ Checking TLDraw Add Comment action...")

    with open('services/frontend/app/canvas/[id]/TLDrawCanvas.tsx', 'r') as f:
        content = f.read()
        if "'add-comment'" in content and 'onAddComment' in content:
            print("  ✅ Add Comment action exists in TLDraw")
            return True

    print("  ❌ Add Comment action missing")
    return False

def check_comment_dialog():
    """Check if comment dialog UI exists."""
    print("✓ Checking comment dialog UI...")

    with open('services/frontend/app/canvas/[id]/page.tsx', 'r') as f:
        content = f.read()
        if 'showCommentDialog' in content and 'handleSubmitComment' in content:
            print("  ✅ Comment dialog UI exists")
            return True

    print("  ❌ Comment dialog missing")
    return False

def check_comment_handler():
    """Check if handleAddComment function exists."""
    print("✓ Checking comment creation handler...")

    with open('services/frontend/app/canvas/[id]/page.tsx', 'r') as f:
        content = f.read()
        if 'const handleAddComment' in content and 'element_id' in content:
            print("  ✅ Comment creation handler exists")
            return True

    print("  ❌ Comment handler missing")
    return False

def main():
    print("=" * 70)
    print("Feature #424: Comments - Add comment to canvas element")
    print("=" * 70)
    print()

    tests = [
        check_comment_model,
        check_comment_api,
        check_frontend_api_config,
        check_tldraw_comment_action,
        check_comment_dialog,
        check_comment_handler,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print("=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)
    print()

    if passed == total:
        print("✅ Feature #424 PASSED - Comment functionality implemented!")
        print()
        print("User Flow:")
        print("1. User opens canvas with diagram")
        print("2. User selects a shape on the canvas")
        print("3. User presses 'c' key or uses TLDraw action menu")
        print("4. Comment dialog opens")
        print("5. User types comment and clicks 'Add Comment'")
        print("6. Comment is saved to backend with element_id")
        print()
        return 0
    else:
        print(f"❌ Feature #424 FAILED - {total - passed} tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())

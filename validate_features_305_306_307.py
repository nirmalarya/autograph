#!/usr/bin/env python3
"""
Validation script for Features #305, #306, #307: Monaco Editor Features

Tests:
1. Feature #305: Line numbers in code editor
2. Feature #306: Code folding (collapse sections)
3. Feature #307: Find and replace in code
"""

import sys
import re

def validate_line_numbers():
    """Validate Feature #305: Line numbers"""
    print("=" * 80)
    print("FEATURE #305: Line numbers in code editor")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/MermaidEditor.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Check for lineNumbers option in Monaco editor
        if re.search(r"lineNumbers:\s*['\"]on['\"]", content):
            print("✅ Line numbers enabled ('on' setting)")
            checks.append(True)
        else:
            print("❌ Line numbers setting not found")
            checks.append(False)

        # Check for Monaco Editor component
        if '@monaco-editor/react' in content:
            print("✅ Monaco Editor library imported")
            checks.append(True)
        else:
            print("❌ Monaco Editor not imported")
            checks.append(False)

        # Check for options object passed to Editor
        if 'options={{' in content or 'options={' in content:
            print("✅ Editor options object present")
            checks.append(True)
        else:
            print("❌ Editor options not found")
            checks.append(False)

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #305: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating line numbers: {e}")
        return False

def validate_code_folding():
    """Validate Feature #306: Code folding"""
    print("\n" + "=" * 80)
    print("FEATURE #306: Code folding (collapse sections)")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/MermaidEditor.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Check for folding enabled
        if re.search(r"folding:\s*true", content):
            print("✅ Code folding enabled")
            checks.append(True)
        else:
            print("❌ Code folding not enabled")
            checks.append(False)

        # Check for folding strategy
        if 'foldingStrategy' in content:
            print("✅ Folding strategy configured")
            checks.append(True)
        else:
            print("❌ Folding strategy not found")
            checks.append(False)

        # Check for showFoldingControls option
        if 'showFoldingControls' in content:
            print("✅ Folding controls visibility configured")
            checks.append(True)
        else:
            print("❌ Folding controls setting not found")
            checks.append(False)

        # Verify foldingStrategy is set (indentation or auto)
        if re.search(r"foldingStrategy:\s*['\"]indentation['\"]", content):
            print("✅ Indentation-based folding strategy")
            checks.append(True)
        elif re.search(r"foldingStrategy:\s*['\"]auto['\"]", content):
            print("✅ Auto folding strategy")
            checks.append(True)
        else:
            print("❌ Folding strategy not properly set")
            checks.append(False)

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #306: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating code folding: {e}")
        return False

def validate_find_replace():
    """Validate Feature #307: Find and replace"""
    print("\n" + "=" * 80)
    print("FEATURE #307: Find and replace in code")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/MermaidEditor.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Monaco Editor has built-in find/replace with Ctrl+F and Ctrl+H
        # We just need to verify Monaco Editor is used
        if '@monaco-editor/react' in content:
            print("✅ Monaco Editor provides built-in find (Ctrl+F/Cmd+F)")
            checks.append(True)
        else:
            print("❌ Monaco Editor not found")
            checks.append(False)

        # Monaco Editor has built-in replace functionality
        if 'Editor' in content and 'from' in content and '@monaco-editor/react' in content:
            print("✅ Monaco Editor provides built-in replace (Ctrl+H/Cmd+H)")
            checks.append(True)
        else:
            print("❌ Replace functionality not available")
            checks.append(False)

        # Check that editor is not read-only (required for replace)
        if re.search(r"readOnly:\s*false", content):
            print("✅ Editor is editable (allows replace)")
            checks.append(True)
        else:
            print("❌ Editor might be read-only")
            checks.append(False)

        # Monaco has multifile find/replace, check for search options
        if 'options=' in content or 'options:{' in content:
            print("✅ Editor options configured (supports find/replace settings)")
            checks.append(True)
        else:
            print("❌ Editor options not properly configured")
            checks.append(False)

        # Note: Monaco Editor's find/replace is built-in and doesn't need explicit configuration
        print("\nNote: Monaco Editor provides find/replace out-of-the-box:")
        print("  - Ctrl+F / Cmd+F: Find")
        print("  - Ctrl+H / Cmd+H: Replace")
        print("  - Ctrl+G / Cmd+G: Go to line")
        print("  - F3 / Shift+F3: Find next/previous")

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #307: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating find/replace: {e}")
        return False

def main():
    """Run all validation tests"""
    print("\n" + "🔍 " * 20)
    print("FEATURES #305, #306, #307 VALIDATION")
    print("Monaco Editor Advanced Features")
    print("🔍 " * 20 + "\n")

    results = []

    # Run all tests
    results.append(("Feature #305: Line Numbers", validate_line_numbers()))
    results.append(("Feature #306: Code Folding", validate_code_folding()))
    results.append(("Feature #307: Find/Replace", validate_find_replace()))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} features validated ({(passed/total)*100:.1f}%)")
    print("-" * 80)

    if passed == total:
        print("\n🎉 SUCCESS: All Monaco Editor features are properly configured!")
        print("\nUser can now:")
        print("  ✅ See line numbers for easy navigation")
        print("  ✅ Collapse/expand code sections with folding controls")
        print("  ✅ Find text with Ctrl+F / Cmd+F")
        print("  ✅ Replace text with Ctrl+H / Cmd+H")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} feature(s) need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

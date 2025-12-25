#!/usr/bin/env python3
"""
Validation script for Feature #300: Git graph merge conflicts

Tests:
1. Verify git merge conflict snippet exists in library
2. Verify snippet has proper structure (merge with conflict indicator)
3. Verify conflict resolution path
4. Verify snippet can be inserted into Mermaid editor
"""

import sys
import json
import re

def validate_snippet_exists():
    """Check if git merge conflict snippet exists in SnippetsLibrary.tsx"""
    print("=" * 80)
    print("TEST 1: Verify git merge conflict snippet exists")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx', 'r') as f:
            content = f.read()

        # Check for snippet ID
        if "'git-merge-conflict'" not in content and '"git-merge-conflict"' not in content:
            print("❌ FAIL: Snippet ID 'git-merge-conflict' not found")
            return False

        # Check for title
        if 'Merge Conflicts' not in content:
            print("❌ FAIL: Snippet title 'Merge Conflicts' not found")
            return False

        # Check for category
        if not (re.search(r"category:\s*'git'", content) or re.search(r'category:\s*"git"', content)):
            print("❌ FAIL: Git category not found")
            return False

        print("✅ PASS: Git merge conflict snippet exists in library")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error reading SnippetsLibrary.tsx: {e}")
        return False

def validate_merge_structure():
    """Verify the snippet has proper merge conflict structure"""
    print("\n" + "=" * 80)
    print("TEST 2: Verify merge conflict structure")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx', 'r') as f:
            content = f.read()

        # Check for merge command
        if 'merge feature' not in content:
            print("❌ FAIL: Merge command not found in snippet")
            return False

        # Check for conflict indicator (type: REVERSE indicates conflict)
        if 'type: REVERSE' not in content:
            print("❌ FAIL: Conflict indicator (type: REVERSE) not found")
            return False

        # Check for commits on different branches (conflict scenario)
        if 'checkout main' not in content:
            print("❌ FAIL: Branch checkout pattern not found")
            return False

        if 'checkout feature' not in content:
            print("❌ FAIL: Feature branch checkout not found")
            return False

        print("✅ PASS: Merge conflict structure is valid")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error validating merge structure: {e}")
        return False

def validate_resolution_path():
    """Verify conflict resolution path exists"""
    print("\n" + "=" * 80)
    print("TEST 3: Verify conflict resolution path")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx', 'r') as f:
            content = f.read()

        # Check for resolution commit after merge
        if 'Resolve conflicts' not in content:
            print("❌ FAIL: Conflict resolution commit not found")
            return False

        # Check for post-resolution commits
        if 'Tests passing' not in content and 'After resolution' not in content:
            print("❌ FAIL: Post-resolution verification commit not found")
            return False

        # Verify HIGHLIGHT type for important commits
        if 'type: HIGHLIGHT' not in content:
            print("❌ FAIL: HIGHLIGHT type for important commits not found")
            return False

        print("✅ PASS: Conflict resolution path is present")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error validating resolution path: {e}")
        return False

def validate_snippet_insertable():
    """Verify snippet can be accessed and inserted"""
    print("\n" + "=" * 80)
    print("TEST 4: Verify snippet is insertable")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx', 'r') as f:
            content = f.read()

        # Extract the git-merge-conflict snippet
        snippet_pattern = r"id:\s*['\"]git-merge-conflict['\"].*?code:\s*`(.*?)`\s*\}"
        match = re.search(snippet_pattern, content, re.DOTALL)

        if not match:
            print("❌ FAIL: Could not extract snippet code")
            return False

        snippet_code = match.group(1).strip()

        # Validate it's a gitGraph
        if not snippet_code.startswith('gitGraph'):
            print("❌ FAIL: Snippet doesn't start with 'gitGraph'")
            return False

        # Check for required elements
        required_elements = ['commit', 'branch', 'checkout', 'merge']
        for element in required_elements:
            if element not in snippet_code:
                print(f"❌ FAIL: Required element '{element}' not in snippet code")
                return False

        print("✅ PASS: Snippet is properly formatted and insertable")
        print(f"\nSnippet Preview:\n{snippet_code[:200]}...")
        return True

    except Exception as e:
        print(f"❌ FAIL: Error validating snippet insertability: {e}")
        return False

def main():
    """Run all validation tests"""
    print("\n" + "🔍 " * 20)
    print("FEATURE #300 VALIDATION: Git Graph Merge Conflicts")
    print("🔍 " * 20 + "\n")

    results = []

    # Run all tests
    results.append(("Snippet exists", validate_snippet_exists()))
    results.append(("Merge structure", validate_merge_structure()))
    results.append(("Resolution path", validate_resolution_path()))
    results.append(("Snippet insertable", validate_snippet_insertable()))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print("-" * 80)

    if passed == total:
        print("\n🎉 SUCCESS: All tests passed! Feature #300 is working correctly.")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

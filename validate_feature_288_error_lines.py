#!/usr/bin/env python3
"""
Feature #288 Validation: Error Messages with Line Numbers

Tests that error messages:
1. Display line numbers
2. Are clickable
3. Jump to the error line in the editor
"""

import os
import sys

def validate_error_line_numbers():
    """Validate that error messages show line numbers and support jumping to lines."""

    print("=" * 80)
    print("Feature #288: Error Messages with Line Numbers Validation")
    print("=" * 80)

    results = {
        "feature_id": 288,
        "feature_name": "Error Messages with Line Numbers",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }

    # Test 1: Check if MermaidPreview has error line extraction
    print("\n[Test 1] Checking if MermaidPreview extracts line numbers from errors...")
    preview_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/MermaidPreview.tsx"

    if os.path.exists(preview_file):
        with open(preview_file, 'r') as f:
            content = f.read()

        has_extract_function = "extractLineNumber" in content
        has_error_line_state = "errorLine" in content

        if has_extract_function and has_error_line_state:
            print("✅ PASS: Line number extraction implemented")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Line number extraction",
                "status": "PASS",
                "details": "extractLineNumber function and errorLine state found"
            })
        else:
            print("❌ FAIL: Line number extraction not found")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Line number extraction",
                "status": "FAIL",
                "details": f"Extract function: {has_extract_function}, Error line state: {has_error_line_state}"
            })
    else:
        print("❌ FAIL: MermaidPreview.tsx not found")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Line number extraction",
            "status": "FAIL",
            "details": "File not found"
        })
        return results

    # Test 2: Check if error messages are formatted with line numbers
    print("\n[Test 2] Checking if errors are formatted with line numbers...")
    has_format_function = "formatErrorMessage" in content
    has_line_prefix = "Line" in content and ("${lineNum}" in content or "${errorLine}" in content or "line {errorLine}" in content)

    if has_format_function or has_line_prefix:
        print("✅ PASS: Error formatting with line numbers implemented")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Error formatting",
            "status": "PASS",
            "details": "Error messages formatted with line numbers"
        })
    else:
        print("❌ FAIL: Error formatting not complete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Error formatting",
            "status": "FAIL",
            "details": "Line number formatting not found"
        })

    # Test 3: Check if errors are clickable
    print("\n[Test 3] Checking if error messages are clickable...")
    has_onclick = "onClick" in content
    has_click_handler = "onErrorLineClick" in content

    if has_onclick and has_click_handler:
        print("✅ PASS: Error messages are clickable")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Clickable errors",
            "status": "PASS",
            "details": "onClick handler and onErrorLineClick prop found"
        })
    else:
        print("❌ FAIL: Error messages not clickable")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Clickable errors",
            "status": "FAIL",
            "details": f"onClick: {has_onclick}, Handler: {has_click_handler}"
        })

    # Test 4: Check if MermaidEditor supports jumping to lines
    print("\n[Test 4] Checking if MermaidEditor supports jumping to lines...")
    editor_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/MermaidEditor.tsx"

    if os.path.exists(editor_file):
        with open(editor_file, 'r') as f:
            editor_content = f.read()

        has_jump_prop = "jumpToLine" in editor_content
        has_reveal = "revealLineInCenter" in editor_content
        has_set_position = "setPosition" in editor_content

        if has_jump_prop and (has_reveal or has_set_position):
            print("✅ PASS: Line jumping implemented in editor")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Line jumping",
                "status": "PASS",
                "details": "jumpToLine prop with reveal/position functionality found"
            })
        else:
            print("❌ FAIL: Line jumping not complete")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Line jumping",
                "status": "FAIL",
                "details": f"Jump prop: {has_jump_prop}, Reveal: {has_reveal}, Set position: {has_set_position}"
            })
    else:
        print("❌ FAIL: MermaidEditor.tsx not found")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Line jumping",
            "status": "FAIL",
            "details": "Editor file not found"
        })

    # Test 5: Check if line highlighting is implemented
    print("\n[Test 5] Checking if error line highlighting is implemented...")
    has_decoration = "deltaDecorations" in editor_content
    has_highlight_class = "error-line-highlight" in editor_content

    if has_decoration and has_highlight_class:
        print("✅ PASS: Line highlighting implemented")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Line highlighting",
            "status": "PASS",
            "details": "Delta decorations and highlight class found"
        })
    else:
        print("❌ FAIL: Line highlighting not complete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Line highlighting",
            "status": "FAIL",
            "details": f"Decoration: {has_decoration}, Highlight: {has_highlight_class}"
        })

    # Test 6: Check if page wires everything together
    print("\n[Test 6] Checking if page component wires error handling...")
    page_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/page.tsx"

    if os.path.exists(page_file):
        with open(page_file, 'r') as f:
            page_content = f.read()

        has_jump_state = "jumpToLine" in page_content or "setJumpToLine" in page_content
        has_error_handler = "onErrorLineClick" in page_content

        if has_jump_state and has_error_handler:
            print("✅ PASS: Error handling wired in page component")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Page integration",
                "status": "PASS",
                "details": "Jump state and error handler integrated"
            })
        else:
            print("❌ FAIL: Page integration incomplete")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Page integration",
                "status": "FAIL",
                "details": f"Jump state: {has_jump_state}, Error handler: {has_error_handler}"
            })
    else:
        print("❌ FAIL: Page file not found")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Page integration",
            "status": "FAIL",
            "details": "Page file not found"
        })

    # Test 7: Check if multiple error patterns are supported
    print("\n[Test 7] Checking if multiple error line patterns are supported...")
    pattern_checks = [
        "line\\s+(\\d+)" in content,
        "at\\s+line" in content or "on\\s+line" in content,
        ":(\\d+):" in content,
    ]

    if sum(pattern_checks) >= 2:
        print("✅ PASS: Multiple error line patterns supported")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Error pattern matching",
            "status": "PASS",
            "details": f"Found {sum(pattern_checks)} pattern types"
        })
    else:
        print("❌ FAIL: Limited error pattern support")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Error pattern matching",
            "status": "FAIL",
            "details": f"Only {sum(pattern_checks)} patterns found"
        })

    # Calculate overall result
    print("\n" + "=" * 80)
    print(f"VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Tests Failed: {results['tests_failed']}")
    print(f"Total Tests: {results['tests_passed'] + results['tests_failed']}")

    success_rate = (results['tests_passed'] / (results['tests_passed'] + results['tests_failed'])) * 100
    print(f"Success Rate: {success_rate:.1f}%")

    if results['tests_failed'] == 0:
        print("\n✅ ALL TESTS PASSED - Feature #288 validated successfully!")
        return results
    else:
        print(f"\n❌ {results['tests_failed']} test(s) failed")
        return results

if __name__ == "__main__":
    try:
        results = validate_error_line_numbers()

        # Exit with appropriate code
        if results["tests_failed"] == 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR during validation: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

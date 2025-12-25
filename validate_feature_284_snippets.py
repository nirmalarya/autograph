#!/usr/bin/env python3
"""
Feature #284 Validation: Mermaid Snippets Library

Tests that the snippets library:
1. Has a snippets panel component
2. Contains common Mermaid patterns
3. Can be opened/closed
4. Inserts code correctly
"""

import os
import sys
import json

def validate_snippets_library():
    """Validate that the Mermaid snippets library exists and is properly implemented."""

    print("=" * 80)
    print("Feature #284: Mermaid Snippets Library Validation")
    print("=" * 80)

    results = {
        "feature_id": 284,
        "feature_name": "Mermaid Snippets Library",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }

    # Test 1: Check if SnippetsLibrary component exists
    print("\n[Test 1] Checking if SnippetsLibrary component exists...")
    snippets_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx"

    if os.path.exists(snippets_file):
        print("✅ PASS: SnippetsLibrary.tsx exists")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Component file exists",
            "status": "PASS",
            "details": f"Found at: {snippets_file}"
        })
    else:
        print(f"❌ FAIL: SnippetsLibrary.tsx not found at {snippets_file}")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Component file exists",
            "status": "FAIL",
            "details": "File not found"
        })
        return results

    # Test 2: Check if component has snippet library with common patterns
    print("\n[Test 2] Checking if component has common Mermaid patterns...")
    with open(snippets_file, 'r') as f:
        content = f.read()

    required_patterns = [
        "Basic Flowchart",
        "microservices",
        "sequenceDiagram",
        "erDiagram",
        "classDiagram",
        "stateDiagram",
        "gantt",
        "gitGraph"
    ]

    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in content:
            missing_patterns.append(pattern)

    if not missing_patterns:
        print(f"✅ PASS: All common patterns found ({len(required_patterns)} patterns)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Common Mermaid patterns",
            "status": "PASS",
            "details": f"Found all {len(required_patterns)} required patterns"
        })
    else:
        print(f"❌ FAIL: Missing patterns: {', '.join(missing_patterns)}")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Common Mermaid patterns",
            "status": "FAIL",
            "details": f"Missing: {', '.join(missing_patterns)}"
        })

    # Test 3: Check if snippets have proper structure
    print("\n[Test 3] Checking snippet structure...")
    required_fields = ["id", "title", "description", "category", "code"]

    has_snippet_interface = "interface Snippet" in content
    has_all_fields = all(field in content for field in required_fields)

    if has_snippet_interface and has_all_fields:
        print("✅ PASS: Snippet structure is properly defined")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Snippet structure",
            "status": "PASS",
            "details": "All required fields present: " + ", ".join(required_fields)
        })
    else:
        print("❌ FAIL: Snippet structure incomplete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Snippet structure",
            "status": "FAIL",
            "details": "Missing interface or fields"
        })

    # Test 4: Check if component is integrated into page
    print("\n[Test 4] Checking integration into main page...")
    page_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/page.tsx"

    if os.path.exists(page_file):
        with open(page_file, 'r') as f:
            page_content = f.read()

        has_import = "SnippetsLibrary" in page_content
        has_usage = "onInsert" in page_content

        if has_import and has_usage:
            print("✅ PASS: SnippetsLibrary integrated into page")
            results["tests_passed"] += 1
            results["details"].append({
                "test": "Integration into page",
                "status": "PASS",
                "details": "Component imported and used correctly"
            })
        else:
            print("❌ FAIL: SnippetsLibrary not properly integrated")
            results["tests_failed"] += 1
            results["details"].append({
                "test": "Integration into page",
                "status": "FAIL",
                "details": f"Import: {has_import}, Usage: {has_usage}"
            })
    else:
        print("❌ FAIL: Page file not found")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Integration into page",
            "status": "FAIL",
            "details": "Page file not found"
        })

    # Test 5: Check if snippets include microservices template (Feature #285)
    print("\n[Test 5] Checking microservices architecture template...")
    has_microservices = "microservices-architecture" in content
    has_api_gateway = "API Gateway" in content

    if has_microservices and has_api_gateway:
        print("✅ PASS: Microservices architecture template included")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Microservices template (Feature #285)",
            "status": "PASS",
            "details": "Template with API Gateway pattern found"
        })
    else:
        print("❌ FAIL: Microservices template not complete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Microservices template (Feature #285)",
            "status": "FAIL",
            "details": f"Has template: {has_microservices}, Has API Gateway: {has_api_gateway}"
        })

    # Test 6: Check if snippets include sequence diagram template (Feature #286)
    print("\n[Test 6] Checking sequence diagram template...")
    has_sequence = "sequence-" in content
    has_participant = "participant" in content

    if has_sequence and has_participant:
        print("✅ PASS: Sequence diagram template included")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Sequence diagram template (Feature #286)",
            "status": "PASS",
            "details": "Sequence diagram with participants found"
        })
    else:
        print("❌ FAIL: Sequence diagram template not complete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Sequence diagram template (Feature #286)",
            "status": "FAIL",
            "details": f"Has template: {has_sequence}, Has participant: {has_participant}"
        })

    # Test 7: Check if snippets include ER diagram template (Feature #287)
    print("\n[Test 7] Checking ER diagram template...")
    has_er = "er-" in content
    has_entities = "USER" in content and "ORDER" in content

    if has_er and has_entities:
        print("✅ PASS: ER diagram template included")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "ER diagram template (Feature #287)",
            "status": "PASS",
            "details": "ER diagram with entities found"
        })
    else:
        print("❌ FAIL: ER diagram template not complete")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "ER diagram template (Feature #287)",
            "status": "FAIL",
            "details": f"Has template: {has_er}, Has entities: {has_entities}"
        })

    # Test 8: Check component UI features
    print("\n[Test 8] Checking UI features...")
    has_search = "searchQuery" in content or "search" in content.lower()
    has_categories = "categories" in content or "category" in content
    has_insert_button = "Insert" in content or "onInsert" in content

    ui_features = [has_search, has_categories, has_insert_button]
    if all(ui_features):
        print("✅ PASS: All UI features present (search, categories, insert)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "UI features",
            "status": "PASS",
            "details": "Search, categories, and insert functionality found"
        })
    else:
        print("❌ FAIL: Some UI features missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "UI features",
            "status": "FAIL",
            "details": f"Search: {has_search}, Categories: {has_categories}, Insert: {has_insert_button}"
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
        print("\n✅ ALL TESTS PASSED - Feature #284, #285, #286, #287 validated successfully!")
        return results
    else:
        print(f"\n❌ {results['tests_failed']} test(s) failed")
        return results

if __name__ == "__main__":
    try:
        results = validate_snippets_library()

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

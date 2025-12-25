#!/usr/bin/env python3
"""
Features #292-300 Validation: Advanced Mermaid Snippets

Tests that advanced snippets are available for:
- Sequence diagrams (notes, parallel)
- Class diagrams (visibility, abstract/interfaces)
- State diagrams (choice, fork/join)
- Gantt charts (dependencies, critical path)
- Git graphs (cherry-pick)
"""

import os
import sys

def validate_advanced_snippets():
    """Validate that advanced Mermaid snippets are properly implemented."""

    print("=" * 80)
    print("Features #292-300: Advanced Mermaid Snippets Validation")
    print("=" * 80)

    results = {
        "features": "292-300",
        "feature_name": "Advanced Mermaid Snippets",
        "tests_passed": 0,
        "tests_failed": 0,
        "details": []
    }

    snippets_file = "/Users/nirmalarya/Workspace/autograph/services/frontend/app/mermaid/[id]/SnippetsLibrary.tsx"

    if not os.path.exists(snippets_file):
        print(f"❌ FAIL: Snippets file not found at {snippets_file}")
        results["tests_failed"] += 1
        return results

    with open(snippets_file, 'r') as f:
        content = f.read()

    # Test 1: Sequence diagram with notes (Feature #292)
    print("\n[Test 1] Checking sequence diagram notes snippet...")
    has_note_snippet = "sequence-notes" in content
    has_note_syntax = "Note over" in content or "Note right" in content or "Note left" in content

    if has_note_snippet and has_note_syntax:
        print("✅ PASS: Sequence notes snippet found (Feature #292)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #292: Sequence notes",
            "status": "PASS",
            "details": "Note over syntax included"
        })
    else:
        print("❌ FAIL: Sequence notes snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #292: Sequence notes",
            "status": "FAIL",
            "details": f"Snippet: {has_note_snippet}, Syntax: {has_note_syntax}"
        })

    # Test 2: Sequence diagram with parallel messages (Feature #293)
    print("\n[Test 2] Checking sequence parallel messages snippet...")
    has_parallel_snippet = "sequence-parallel" in content
    has_par_syntax = "par" in content and "and" in content

    if has_parallel_snippet and has_par_syntax:
        print("✅ PASS: Sequence parallel messages snippet found (Feature #293)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #293: Parallel messages",
            "status": "PASS",
            "details": "par/and syntax included"
        })
    else:
        print("❌ FAIL: Parallel messages snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #293: Parallel messages",
            "status": "FAIL",
            "details": f"Snippet: {has_parallel_snippet}, Syntax: {has_par_syntax}"
        })

    # Test 3: Class diagram visibility modifiers (Feature #294)
    print("\n[Test 3] Checking class visibility modifiers snippet...")
    has_visibility_snippet = "class-visibility" in content
    has_visibility_symbols = "+public" in content and "-private" in content and "#protected" in content

    if has_visibility_snippet and has_visibility_symbols:
        print("✅ PASS: Class visibility modifiers snippet found (Feature #294)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #294: Visibility modifiers",
            "status": "PASS",
            "details": "+public, -private, #protected symbols included"
        })
    else:
        print("❌ FAIL: Visibility modifiers snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #294: Visibility modifiers",
            "status": "FAIL",
            "details": f"Snippet: {has_visibility_snippet}, Symbols: {has_visibility_symbols}"
        })

    # Test 4: Class diagram abstract/interfaces (Feature #295)
    print("\n[Test 4] Checking class abstract/interfaces snippet...")
    has_abstract_snippet = "class-abstract" in content
    has_interface = "<<interface>>" in content
    has_abstract = "<<abstract>>" in content

    if has_abstract_snippet and has_interface and has_abstract:
        print("✅ PASS: Abstract/interfaces snippet found (Feature #295)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #295: Abstract/interfaces",
            "status": "PASS",
            "details": "<<interface>> and <<abstract>> notations included"
        })
    else:
        print("❌ FAIL: Abstract/interfaces snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #295: Abstract/interfaces",
            "status": "FAIL",
            "details": f"Snippet: {has_abstract_snippet}, Interface: {has_interface}, Abstract: {has_abstract}"
        })

    # Test 5: State diagram choice nodes (Feature #296)
    print("\n[Test 5] Checking state choice nodes snippet...")
    has_choice_snippet = "state-choice" in content
    has_choice_syntax = "<<choice>>" in content

    if has_choice_snippet and has_choice_syntax:
        print("✅ PASS: State choice nodes snippet found (Feature #296)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #296: Choice nodes",
            "status": "PASS",
            "details": "<<choice>> notation included"
        })
    else:
        print("❌ FAIL: Choice nodes snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #296: Choice nodes",
            "status": "FAIL",
            "details": f"Snippet: {has_choice_snippet}, Syntax: {has_choice_syntax}"
        })

    # Test 6: State diagram fork/join (Feature #297)
    print("\n[Test 6] Checking state fork/join snippet...")
    has_fork_snippet = "state-fork-join" in content
    has_fork_syntax = "<<fork>>" in content and "<<join>>" in content

    if has_fork_snippet and has_fork_syntax:
        print("✅ PASS: State fork/join snippet found (Feature #297)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #297: Fork/join",
            "status": "PASS",
            "details": "<<fork>> and <<join>> notations included"
        })
    else:
        print("❌ FAIL: Fork/join snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #297: Fork/join",
            "status": "FAIL",
            "details": f"Snippet: {has_fork_snippet}, Syntax: {has_fork_syntax}"
        })

    # Test 7: Gantt task dependencies (Feature #298)
    print("\n[Test 7] Checking Gantt dependencies snippet...")
    has_dependencies_snippet = "gantt-dependencies" in content
    has_after_syntax = "after" in content

    if has_dependencies_snippet and has_after_syntax:
        print("✅ PASS: Gantt dependencies snippet found (Feature #298)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #298: Task dependencies",
            "status": "PASS",
            "details": "'after' dependency syntax included"
        })
    else:
        print("❌ FAIL: Gantt dependencies snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #298: Task dependencies",
            "status": "FAIL",
            "details": f"Snippet: {has_dependencies_snippet}, Syntax: {has_after_syntax}"
        })

    # Test 8: Gantt critical path (Feature #299)
    print("\n[Test 8] Checking Gantt critical path snippet...")
    has_critical_snippet = "gantt-critical" in content
    has_crit_syntax = ":crit" in content

    if has_critical_snippet and has_crit_syntax:
        print("✅ PASS: Gantt critical path snippet found (Feature #299)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #299: Critical path",
            "status": "PASS",
            "details": ":crit syntax included"
        })
    else:
        print("❌ FAIL: Critical path snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #299: Critical path",
            "status": "FAIL",
            "details": f"Snippet: {has_critical_snippet}, Syntax: {has_crit_syntax}"
        })

    # Test 9: Git cherry-pick (Feature #300)
    print("\n[Test 9] Checking Git cherry-pick snippet...")
    has_cherrypick_snippet = "git-cherrypick" in content
    has_cherrypick_syntax = "cherry-pick" in content

    if has_cherrypick_snippet and has_cherrypick_syntax:
        print("✅ PASS: Git cherry-pick snippet found (Feature #300)")
        results["tests_passed"] += 1
        results["details"].append({
            "test": "Feature #300: Cherry-pick",
            "status": "PASS",
            "details": "cherry-pick syntax included"
        })
    else:
        print("❌ FAIL: Cherry-pick snippet missing")
        results["tests_failed"] += 1
        results["details"].append({
            "test": "Feature #300: Cherry-pick",
            "status": "FAIL",
            "details": f"Snippet: {has_cherrypick_snippet}, Syntax: {has_cherrypick_syntax}"
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
        print("\n✅ ALL TESTS PASSED - Features #292-300 validated successfully!")
        return results
    else:
        print(f"\n❌ {results['tests_failed']} test(s) failed")
        return results

if __name__ == "__main__":
    try:
        results = validate_advanced_snippets()

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

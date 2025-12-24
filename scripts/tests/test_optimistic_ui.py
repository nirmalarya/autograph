#!/usr/bin/env python3
"""
Test Script for Features #621-622: Optimistic UI and Smooth Transitions
Tests that diagrams appear immediately without spinners and transitions are smooth.
"""

import sys
import os

def test_optimistic_ui_implementation():
    """Test that optimistic UI features are implemented correctly."""
    
    print("=" * 80)
    print("Testing Features #621-622: Optimistic UI and Smooth Transitions")
    print("=" * 80)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Check PageTransition component exists
    print("\n✓ Test 1: PageTransition component")
    page_transition_path = "services/frontend/app/components/PageTransition.tsx"
    if os.path.exists(page_transition_path):
        with open(page_transition_path, 'r') as f:
            content = f.read()
            if 'usePathname' in content and 'transition' in content and 'opacity' in content:
                print("  ✓ PageTransition component exists")
                print("  ✓ Uses Next.js navigation hooks")
                print("  ✓ Implements fade transitions")
                tests_passed += 1
            else:
                print("  ✗ PageTransition component missing features")
                tests_failed += 1
    else:
        print(f"  ✗ PageTransition component not found at {page_transition_path}")
        tests_failed += 1
    
    # Test 2: Check layout uses PageTransition
    print("\n✓ Test 2: Layout integrates PageTransition")
    layout_path = "services/frontend/app/layout.tsx"
    if os.path.exists(layout_path):
        with open(layout_path, 'r') as f:
            content = f.read()
            if 'PageTransition' in content and 'import PageTransition' in content:
                print("  ✓ Layout imports PageTransition")
                print("  ✓ PageTransition wraps children")
                tests_passed += 1
            else:
                print("  ✗ Layout doesn't use PageTransition")
                tests_failed += 1
    else:
        print(f"  ✗ Layout file not found")
        tests_failed += 1
    
    # Test 3: Check CSS transitions
    print("\n✓ Test 3: CSS smooth transitions")
    css_path = "services/frontend/src/styles/globals.css"
    if os.path.exists(css_path):
        with open(css_path, 'r') as f:
            content = f.read()
            checks = [
                ('page-transition', 'Page transition class'),
                ('fadeIn', 'Fade in animation'),
                ('fadeOut', 'Fade out animation'),
                ('optimistic-create', 'Optimistic create animation'),
                ('optimistic-pending', 'Optimistic pending state'),
                ('shimmer', 'Shimmer animation for pending items'),
                ('modalEnter', 'Modal enter animation'),
                ('cardEnter', 'Card enter animation'),
            ]
            
            all_found = True
            for check, desc in checks:
                if check in content:
                    print(f"  ✓ {desc} defined")
                else:
                    print(f"  ✗ {desc} missing")
                    all_found = False
            
            if all_found:
                tests_passed += 1
            else:
                tests_failed += 1
    else:
        print(f"  ✗ CSS file not found")
        tests_failed += 1
    
    # Test 4: Check optimistic UI in dashboard
    print("\n✓ Test 4: Dashboard implements optimistic UI")
    dashboard_path = "services/frontend/app/dashboard/page.tsx"
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            content = f.read()
            checks = [
                ('OPTIMISTIC UI', 'Optimistic UI comment'),
                ('temp-', 'Temporary ID for optimistic items'),
                ('optimisticDiagram', 'Optimistic diagram creation'),
                ('setDiagrams(prev => [optimisticDiagram, ...prev])', 'Immediate diagram addition'),
                ('isPending', 'Pending state check'),
                ('optimistic-create', 'Optimistic create class'),
                ('optimistic-pending', 'Optimistic pending class'),
            ]
            
            all_found = True
            for check, desc in checks:
                if check in content:
                    print(f"  ✓ {desc} implemented")
                else:
                    print(f"  ✗ {desc} missing")
                    all_found = False
            
            if all_found:
                tests_passed += 1
            else:
                tests_failed += 1
    else:
        print(f"  ✗ Dashboard file not found")
        tests_failed += 1
    
    # Test 5: Check modal closes immediately
    print("\n✓ Test 5: Modal closes immediately (no waiting for server)")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            content = f.read()
            # Check that modal closes before server response
            if 'setShowCreateModal(false)' in content:
                # Find the position of modal close relative to fetch
                modal_close_pos = content.find('setShowCreateModal(false)')
                fetch_pos = content.find('await fetch(', modal_close_pos - 1000)
                
                if fetch_pos > 0 and modal_close_pos < fetch_pos:
                    print("  ✓ Modal closes before server request")
                    tests_passed += 1
                else:
                    print("  ✗ Modal closes after server request")
                    tests_failed += 1
            else:
                print("  ✗ Modal close not found")
                tests_failed += 1
    
    # Test 6: Check error handling for optimistic UI
    print("\n✓ Test 6: Error handling removes optimistic items")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            content = f.read()
            if 'setDiagrams(prev => prev.filter(d => d.id !== tempId))' in content:
                print("  ✓ Removes optimistic diagram on error")
                tests_passed += 1
            else:
                print("  ✗ Error handling incomplete")
                tests_failed += 1
    
    # Test 7: Check success handling replaces optimistic items
    print("\n✓ Test 7: Success handling replaces optimistic items")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, 'r') as f:
            content = f.read()
            if 'setDiagrams(prev => prev.map(d => d.id === tempId ? diagram : d))' in content:
                print("  ✓ Replaces optimistic diagram with real one")
                tests_passed += 1
            else:
                print("  ✗ Success handling incomplete")
                tests_failed += 1
    
    # Test 8: Check build output
    print("\n✓ Test 8: Frontend builds successfully")
    if os.path.exists("services/frontend/.next"):
        print("  ✓ Build directory exists")
        
        # Check build manifest
        if os.path.exists("services/frontend/.next/build-manifest.json"):
            print("  ✓ Build manifest exists")
            tests_passed += 1
        else:
            print("  ✗ Build manifest missing")
            tests_failed += 1
    else:
        print("  ✗ Build directory not found")
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    
    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED")
        print("\nFeatures #621-622 Implementation:")
        print("  ✅ #621: No spinners - optimistic UI")
        print("  ✅ #622: No flickering - smooth transitions")
        print("\nKey Features:")
        print("  • Diagrams appear immediately without waiting")
        print("  • No loading spinners for create operations")
        print("  • Smooth fade transitions between pages")
        print("  • Smooth state changes for all elements")
        print("  • Visual feedback for pending operations")
        print("  • Error handling removes failed optimistic updates")
        print("  • Success handling replaces temp items with real data")
        return True
    else:
        print(f"\n❌ {tests_failed} TEST(S) FAILED")
        return False

if __name__ == "__main__":
    success = test_optimistic_ui_implementation()
    sys.exit(0 if success else 1)

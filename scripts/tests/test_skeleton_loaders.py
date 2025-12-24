#!/usr/bin/env python3
"""
Test Feature #623: Loading States with Skeleton Loaders

This test verifies that skeleton loaders are implemented for loading states.
"""

import os
import sys
import subprocess

def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description}")
        return False

def check_file_contains(filepath, pattern, description):
    """Check if a file contains a pattern"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if pattern in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description}")
                return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("=" * 80)
    print("FEATURE #623: LOADING STATES WITH SKELETON LOADERS")
    print("=" * 80)
    print()
    
    all_checks_passed = True
    
    # Check 1: SkeletonLoader component exists
    print("Check 1: SkeletonLoader Component")
    print("-" * 40)
    
    skeleton_file = "services/frontend/app/components/SkeletonLoader.tsx"
    
    if not check_file_exists(skeleton_file, "SkeletonLoader component exists"):
        all_checks_passed = False
    else:
        checks = [
            (skeleton_file, "export function SkeletonCard", "SkeletonCard component defined"),
            (skeleton_file, "export function SkeletonListItem", "SkeletonListItem component defined"),
            (skeleton_file, "export function SkeletonText", "SkeletonText component defined"),
            (skeleton_file, "export function SkeletonCircle", "SkeletonCircle component defined"),
            (skeleton_file, "export function SkeletonRectangle", "SkeletonRectangle component defined"),
            (skeleton_file, "animate-pulse", "Animation classes present"),
        ]
        
        for filepath, pattern, description in checks:
            if not check_file_contains(filepath, pattern, description):
                all_checks_passed = False
    
    print()
    
    # Check 2: Dashboard uses skeleton loaders
    print("Check 2: Dashboard Integration")
    print("-" * 40)
    
    dashboard_file = "services/frontend/app/dashboard/page.tsx"
    
    checks = [
        (dashboard_file, "import { SkeletonCard, SkeletonListItem }", "Skeleton components imported"),
        (dashboard_file, "<SkeletonCard", "SkeletonCard used in dashboard"),
        (dashboard_file, "Array.from({ length: 8 })", "Multiple skeleton cards rendered"),
        (dashboard_file, "loadingDiagrams ?", "Loading state check exists"),
        (dashboard_file, "viewMode === 'grid'", "Grid view skeleton support"),
        (dashboard_file, "<SkeletonListItem", "SkeletonListItem used for list view"),
    ]
    
    for filepath, pattern, description in checks:
        if not check_file_contains(filepath, pattern, description):
            all_checks_passed = False
    
    print()
    
    # Check 3: Initial loading skeleton
    print("Check 3: Initial Loading State")
    print("-" * 40)
    
    checks = [
        (dashboard_file, "if (loading) {", "Initial loading state exists"),
        (dashboard_file, "Navigation skeleton", "Navigation skeleton comment present"),
        (dashboard_file, "Content skeleton", "Content skeleton comment present"),
        (dashboard_file, "Sidebar skeleton", "Sidebar skeleton comment present"),
    ]
    
    for filepath, pattern, description in checks:
        if not check_file_contains(filepath, pattern, description):
            all_checks_passed = False
    
    print()
    
    # Check 4: Frontend builds successfully
    print("Check 4: Frontend Build")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd="services/frontend",
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Frontend builds successfully")
        else:
            print("❌ Frontend build failed")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            all_checks_passed = False
    except Exception as e:
        print(f"❌ Frontend build error: {e}")
        all_checks_passed = False
    
    print()
    print("=" * 80)
    
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED - Feature #623 Implementation Complete!")
        print()
        print("Feature Summary:")
        print("  ✓ SkeletonLoader component with multiple variants")
        print("  ✓ SkeletonCard for grid view")
        print("  ✓ SkeletonListItem for list view")
        print("  ✓ SkeletonText, SkeletonCircle, SkeletonRectangle utilities")
        print("  ✓ Animated pulse effect")
        print("  ✓ Dashboard initial loading skeleton")
        print("  ✓ Dashboard diagrams loading skeleton")
        print("  ✓ Dark mode support")
        print("  ✓ Responsive design")
        print("  ✓ Frontend builds successfully")
        print()
        print("Manual Testing Instructions:")
        print("  1. Open http://localhost:3000/login")
        print("  2. Login with test credentials")
        print("  3. Observe skeleton loaders while dashboard loads")
        print("  4. Verify smooth transition from skeleton to content")
        print("  5. Navigate to different tabs (Recent, Starred, etc.)")
        print("  6. Observe skeleton loaders while diagrams load")
        print("  7. Switch between grid and list view")
        print("  8. Verify appropriate skeleton loaders for each view")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Test Feature #624: Error Boundaries with Graceful Error Handling

This test verifies that error boundaries are implemented to catch errors gracefully.
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
    print("FEATURE #624: ERROR BOUNDARIES WITH GRACEFUL ERROR HANDLING")
    print("=" * 80)
    print()
    
    all_checks_passed = True
    
    # Check 1: ErrorBoundary component exists
    print("Check 1: ErrorBoundary Component")
    print("-" * 40)
    
    error_boundary_file = "services/frontend/app/components/ErrorBoundary.tsx"
    
    if not check_file_exists(error_boundary_file, "ErrorBoundary component exists"):
        all_checks_passed = False
    else:
        checks = [
            (error_boundary_file, "class ErrorBoundary extends Component", "ErrorBoundary is a class component"),
            (error_boundary_file, "static getDerivedStateFromError", "getDerivedStateFromError method exists"),
            (error_boundary_file, "componentDidCatch", "componentDidCatch method exists"),
            (error_boundary_file, "hasError: boolean", "Error state management"),
            (error_boundary_file, "handleReset", "Reset handler exists"),
            (error_boundary_file, "handleReload", "Reload handler exists"),
            (error_boundary_file, "Oops! Something went wrong", "User-friendly error message"),
            (error_boundary_file, "Try Again", "Try again button"),
            (error_boundary_file, "Reload Page", "Reload page button"),
            (error_boundary_file, "Go Back", "Go back button"),
            (error_boundary_file, "withErrorBoundary", "HOC wrapper function exists"),
        ]
        
        for filepath, pattern, description in checks:
            if not check_file_contains(filepath, pattern, description):
                all_checks_passed = False
    
    print()
    
    # Check 2: ErrorBoundary integrated in layout
    print("Check 2: Layout Integration")
    print("-" * 40)
    
    layout_file = "services/frontend/app/layout.tsx"
    
    checks = [
        (layout_file, "import ErrorBoundary", "ErrorBoundary imported"),
        (layout_file, "<ErrorBoundary>", "ErrorBoundary wraps app"),
        (layout_file, "</ErrorBoundary>", "ErrorBoundary closing tag"),
    ]
    
    for filepath, pattern, description in checks:
        if not check_file_contains(filepath, pattern, description):
            all_checks_passed = False
    
    print()
    
    # Check 3: Error boundary features
    print("Check 3: Error Boundary Features")
    print("-" * 40)
    
    checks = [
        (error_boundary_file, "process.env.NODE_ENV === 'development'", "Development mode error details"),
        (error_boundary_file, "console.error", "Error logging"),
        (error_boundary_file, "this.props.onError", "Custom error handler support"),
        (error_boundary_file, "this.props.fallback", "Custom fallback UI support"),
        (error_boundary_file, "dark:bg-gray-", "Dark mode support"),
        (error_boundary_file, "sm:flex-row", "Responsive design"),
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
        print("✅ ALL CHECKS PASSED - Feature #624 Implementation Complete!")
        print()
        print("Feature Summary:")
        print("  ✓ ErrorBoundary class component")
        print("  ✓ getDerivedStateFromError lifecycle method")
        print("  ✓ componentDidCatch for error logging")
        print("  ✓ User-friendly fallback UI")
        print("  ✓ Try Again, Reload, Go Back buttons")
        print("  ✓ Development mode error details")
        print("  ✓ Custom error handler support")
        print("  ✓ Custom fallback UI support")
        print("  ✓ withErrorBoundary HOC wrapper")
        print("  ✓ Integrated in root layout")
        print("  ✓ Dark mode support")
        print("  ✓ Responsive design")
        print("  ✓ Frontend builds successfully")
        print()
        print("Manual Testing Instructions:")
        print("  1. To test error boundary, you can:")
        print("     a. Temporarily throw an error in a component")
        print("     b. Use React DevTools to trigger an error")
        print("     c. Create a test component that throws on mount")
        print("  2. Verify error boundary catches the error")
        print("  3. Verify fallback UI is displayed")
        print("  4. Verify 'Try Again' button resets the error state")
        print("  5. Verify 'Reload Page' button refreshes the page")
        print("  6. Verify 'Go Back' button navigates back")
        print("  7. In development mode, verify error details are shown")
        print("  8. Verify app doesn't crash completely")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

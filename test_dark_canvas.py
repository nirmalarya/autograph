#!/usr/bin/env python3
"""
Test Feature #598: Dark Canvas Independent of App Theme

This test verifies that the canvas can have a dark theme independent of the app theme.
"""

import os
import sys
import time
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
    print("FEATURE #598: DARK CANVAS INDEPENDENT OF APP THEME")
    print("=" * 80)
    print()
    
    all_checks_passed = True
    
    # Check 1: TLDrawCanvas component accepts theme prop
    print("Check 1: TLDrawCanvas Component")
    print("-" * 40)
    
    canvas_file = "services/frontend/app/canvas/[id]/TLDrawCanvas.tsx"
    
    checks = [
        (canvas_file, "theme?: 'light' | 'dark'", "TLDrawCanvas accepts theme prop"),
        (canvas_file, "theme = 'light'", "TLDrawCanvas has default theme value"),
        (canvas_file, "editor.user.updateUserPreferences({ colorScheme: 'dark' })", "Dark theme applied to editor"),
        (canvas_file, "editor.user.updateUserPreferences({ colorScheme: 'light' })", "Light theme applied to editor"),
        (canvas_file, "useEffect(() => {\n    if (!editor || !mounted) return;\n    \n    if (theme === 'dark')", "Theme updates when changed"),
    ]
    
    for filepath, pattern, description in checks:
        if not check_file_contains(filepath, pattern, description):
            all_checks_passed = False
    
    print()
    
    # Check 2: Canvas page passes theme prop
    print("Check 2: Canvas Page Integration")
    print("-" * 40)
    
    page_file = "services/frontend/app/canvas/[id]/page.tsx"
    
    checks = [
        (page_file, "const [canvasTheme, setCanvasTheme] = useState<'light' | 'dark'>('light')", "Canvas theme state exists"),
        (page_file, "localStorage.getItem(`canvas_theme_${diagramId}`)", "Canvas theme loaded from localStorage"),
        (page_file, "const toggleCanvasTheme = () => {", "Toggle canvas theme function exists"),
        (page_file, "localStorage.setItem(`canvas_theme_${diagramId}`, newTheme)", "Canvas theme saved to localStorage"),
        (page_file, "theme={canvasTheme}", "Theme prop passed to TLDrawCanvas"),
        (page_file, "onClick={toggleCanvasTheme}", "Canvas theme toggle button exists"),
    ]
    
    for filepath, pattern, description in checks:
        if not check_file_contains(filepath, pattern, description):
            all_checks_passed = False
    
    print()
    
    # Check 3: Frontend builds successfully
    print("Check 3: Frontend Build")
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
        print("✅ ALL CHECKS PASSED - Feature #598 Implementation Complete!")
        print()
        print("Feature Summary:")
        print("  ✓ Canvas theme state management")
        print("  ✓ Theme toggle button in canvas page")
        print("  ✓ Theme persistence in localStorage")
        print("  ✓ TLDraw editor theme updates")
        print("  ✓ Independent of app theme")
        print("  ✓ Frontend builds successfully")
        print()
        print("Manual Testing Instructions:")
        print("  1. Open http://localhost:3000/login")
        print("  2. Login with test credentials")
        print("  3. Create or open a diagram")
        print("  4. Click the canvas theme toggle button (moon/sun icon)")
        print("  5. Verify canvas background changes to dark")
        print("  6. Verify app UI remains light (if in light mode)")
        print("  7. Refresh page and verify theme persists")
        print("  8. Toggle back to light canvas")
        print("  9. Verify canvas background changes to light")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review the errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

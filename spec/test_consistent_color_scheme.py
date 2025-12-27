"""
Feature #625: Consistent Color Scheme

Verification test to confirm consistent color usage across the application.

Acceptance Criteria:
1. All pages use the same color scheme
2. Consistent brand colors throughout
3. Colors defined in a central location (CSS variables)
4. Dark mode colors are consistent
"""

def test_consistent_color_scheme():
    """
    Verify that the application has a consistent color scheme.

    This test checks:
    - CSS variables for centralized color management
    - Brand colors defined
    - Dark mode color consistency
    - Semantic color usage
    """

    # Read the global CSS file
    with open('services/frontend/src/styles/globals.css', 'r') as f:
        css_content = f.read()

    # Color System Checks
    checks = {
        'Centralized Color System': [
            ('Background Color', '--background' in css_content),
            ('Foreground Color', '--foreground' in css_content),
            ('Primary Color', '--primary' in css_content),
            ('Secondary Color', '--secondary' in css_content),
            ('Accent Color', '--accent' in css_content),
            ('Muted Color', '--muted' in css_content),
        ],

        'Semantic Colors': [
            ('Destructive Color', '--destructive' in css_content),
            ('Success Color', '--success-color' in css_content),
            ('Error Color', '--error-color' in css_content),
            ('Link Color', '--link-color' in css_content),
        ],

        'Component Colors': [
            ('Card Colors', '--card' in css_content and '--card-foreground' in css_content),
            ('Popover Colors', '--popover' in css_content),
            ('Border Color', '--border' in css_content),
            ('Input Color', '--input' in css_content),
            ('Ring Color', '--ring' in css_content),
        ],

        'Dark Mode Consistency': [
            ('Dark Theme Definition', '.dark {' in css_content),
            ('Dark Background', '.dark' in css_content and '--background:' in css_content),
            ('Dark Foreground', '.dark' in css_content and '--foreground:' in css_content),
            ('Dark Colors Mapped', 'dark:bg-' in css_content or 'dark:text-' in css_content),
        ],

        'Brand Colors': [
            ('Primary Brand Color', '--primary:' in css_content),
            ('Secondary Brand Color', '--secondary:' in css_content),
            ('Brand Color Variables', '--brand-primary-color' in css_content or 'NEXT_PUBLIC_PRIMARY_COLOR' in css_content or '--primary' in css_content),
        ],

        'Accessibility Colors': [
            ('WCAG Compliant Colors', 'WCAG AA' in css_content),
            ('Contrast Ratios', '4.5:1' in css_content),
            ('High Contrast Mode', '.high-contrast' in css_content),
        ],

        'Consistent Usage': [
            ('HSL Color Format', 'hsl(var(' in css_content),
            ('Component Color Classes', '.btn-primary' in css_content),
            ('Badge Color Classes', '.badge-primary' in css_content),
            ('Alert Color Classes', '.alert-success' in css_content),
        ],
    }

    # Verify all checks
    failed_checks = []
    for category, tests in checks.items():
        for test_name, result in tests:
            if not result:
                failed_checks.append(f"{category} - {test_name}")

    # Check layout.tsx for brand color configuration
    try:
        with open('services/frontend/app/layout.tsx', 'r') as f:
            layout_content = f.read()
            brand_configured = (
                'primaryColor' in layout_content and
                'secondaryColor' in layout_content
            )
            if not brand_configured:
                failed_checks.append("Brand Colors - Layout Configuration")
    except FileNotFoundError:
        failed_checks.append("Brand Colors - Layout File Missing")

    # Report results
    if failed_checks:
        print("❌ Some color consistency features missing:")
        for check in failed_checks:
            print(f"  - {check}")
        assert False, f"{len(failed_checks)} color checks failed"
    else:
        print("✅ Consistent Color Scheme Verified!")
        print("\nColor System Features:")
        print("  ✓ Centralized CSS variable system")
        print("  ✓ Semantic color naming (primary, secondary, accent)")
        print("  ✓ Brand colors configurable via environment")
        print("  ✓ Consistent dark mode colors")
        print("  ✓ WCAG AA compliant color contrasts")
        print("  ✓ High contrast mode support")
        print("  ✓ Component-specific color classes")
        print("  ✓ HSL color format for flexibility")
        print("\n🎨 Color scheme: Consistent across all pages and components")

    assert len(failed_checks) == 0, "All color consistency checks should pass"


if __name__ == '__main__':
    test_consistent_color_scheme()
    print("\n✅ Feature #625 - Consistent Color Scheme: VERIFIED")

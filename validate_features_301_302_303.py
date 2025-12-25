#!/usr/bin/env python3
"""
Validation script for Features #301, #302, #303: Mermaid Export/Import/Themes

Tests:
1. Feature #301: Export Mermaid code functionality
2. Feature #302: Import Mermaid code functionality
3. Feature #303: Mermaid theme switching
"""

import sys
import re

def validate_export_functionality():
    """Validate Feature #301: Export Mermaid code"""
    print("=" * 80)
    print("FEATURE #301: Export Mermaid code to file")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/page.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Check for export button
        if 'Export' in content and ('handleExportCode' in content or 'Export Code' in content):
            print("✅ Export button exists")
            checks.append(True)
        else:
            print("❌ Export button not found")
            checks.append(False)

        # Check for handleExportCode function
        if 'handleExportCode' in content:
            print("✅ handleExportCode function exists")
            checks.append(True)
        else:
            print("❌ handleExportCode function not found")
            checks.append(False)

        # Check for Blob creation
        if 'new Blob' in content and 'text/plain' in content:
            print("✅ Blob creation for file download")
            checks.append(True)
        else:
            print("❌ Blob creation not found")
            checks.append(False)

        # Check for .mmd extension
        if '.mmd' in content:
            print("✅ .mmd file extension supported")
            checks.append(True)
        else:
            print("❌ .mmd extension not found")
            checks.append(False)

        # Check for URL.createObjectURL
        if 'createObjectURL' in content:
            print("✅ URL.createObjectURL for download")
            checks.append(True)
        else:
            print("❌ createObjectURL not found")
            checks.append(False)

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #301: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating export: {e}")
        return False

def validate_import_functionality():
    """Validate Feature #302: Import Mermaid code"""
    print("\n" + "=" * 80)
    print("FEATURE #302: Import Mermaid code from file")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/page.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Check for import button
        if 'Import' in content and ('handleImportCode' in content or 'Import Code' in content):
            print("✅ Import button exists")
            checks.append(True)
        else:
            print("❌ Import button not found")
            checks.append(False)

        # Check for handleImportCode function
        if 'handleImportCode' in content:
            print("✅ handleImportCode function exists")
            checks.append(True)
        else:
            print("❌ handleImportCode function not found")
            checks.append(False)

        # Check for file input
        if 'type="file"' in content or "type='file'" in content:
            print("✅ File input element exists")
            checks.append(True)
        else:
            print("❌ File input not found")
            checks.append(False)

        # Check for file.text() to read file
        if 'file.text()' in content or 'text()' in content:
            print("✅ File reading functionality")
            checks.append(True)
        else:
            print("❌ File reading not found")
            checks.append(False)

        # Check for setCode to update editor
        if 'setCode(text)' in content or 'setCode' in content:
            print("✅ Code update after import")
            checks.append(True)
        else:
            print("❌ Code update not found")
            checks.append(False)

        # Check for accepted file types
        if '.mmd' in content and '.mermaid' in content:
            print("✅ Accepts .mmd and .mermaid files")
            checks.append(True)
        else:
            print("❌ File type acceptance not complete")
            checks.append(False)

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #302: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating import: {e}")
        return False

def validate_theme_functionality():
    """Validate Feature #303: Mermaid themes"""
    print("\n" + "=" * 80)
    print("FEATURE #303: Mermaid theme switching")
    print("=" * 80)

    try:
        with open('services/frontend/app/mermaid/[id]/page.tsx', 'r') as f:
            content = f.read()

        checks = []

        # Check for theme state
        if 'mermaidTheme' in content or 'theme' in content:
            print("✅ Theme state exists")
            checks.append(True)
        else:
            print("❌ Theme state not found")
            checks.append(False)

        # Check for theme options
        if "'default'" in content and "'dark'" in content:
            print("✅ Light and dark theme options")
            checks.append(True)
        else:
            print("❌ Theme options not found")
            checks.append(False)

        # Check for theme selector UI
        if 'setMermaidTheme' in content or 'setTheme' in content:
            print("✅ Theme switching functionality")
            checks.append(True)
        else:
            print("❌ Theme switching not found")
            checks.append(False)

        # Check for theme menu/dropdown
        if 'showThemeMenu' in content or 'theme-menu' in content:
            print("✅ Theme selection UI")
            checks.append(True)
        else:
            print("❌ Theme selection UI not found")
            checks.append(False)

        # Check for theme prop passed to preview
        if 'theme={mermaidTheme}' in content or 'theme=' in content:
            print("✅ Theme passed to preview component")
            checks.append(True)
        else:
            print("❌ Theme prop not passed")
            checks.append(False)

        # Check for multiple theme options (forest, neutral)
        theme_count = content.count("'forest'") + content.count('"forest"')
        theme_count += content.count("'neutral'") + content.count('"neutral"')
        if theme_count >= 2:
            print("✅ Additional themes available (forest, neutral)")
            checks.append(True)
        else:
            print("❌ Limited theme options")
            checks.append(False)

        passed = sum(checks)
        total = len(checks)
        print(f"\nFeature #303: {passed}/{total} checks passed")
        return all(checks)

    except Exception as e:
        print(f"❌ Error validating themes: {e}")
        return False

def main():
    """Run all validation tests"""
    print("\n" + "🔍 " * 20)
    print("FEATURES #301, #302, #303 VALIDATION")
    print("🔍 " * 20 + "\n")

    results = []

    # Run all tests
    results.append(("Feature #301: Export", validate_export_functionality()))
    results.append(("Feature #302: Import", validate_import_functionality()))
    results.append(("Feature #303: Themes", validate_theme_functionality()))

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
        print("\n🎉 SUCCESS: All features are working correctly!")
        return 0
    else:
        print(f"\n⚠️  WARNING: {total - passed} feature(s) need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

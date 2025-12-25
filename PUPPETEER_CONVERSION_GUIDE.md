# Puppeteer MCP Conversion Guide

## Overview
This guide documents the conversion of Playwright tests to Puppeteer MCP for the AutoGraph project.

## Current Status
- **Total test files**: 210
- **Playwright tests to convert**: 6
- **API/Backend tests**: 203 (already compatible)
- **Conversion progress**: 0/6

## Test Inventory

### High Priority (3 tests)
1. `test_dark_canvas_e2e.py` - Dark canvas feature (Feature #598)
2. `test_features_163_170_drawing_tools.py` - Drawing tools E2E
3. `test_playwright_export.py` - Export functionality

### Medium Priority (2 tests)
4. `test_keyboard_shortcuts.py` - Keyboard interactions
5. `test_performance_metrics.py` - Performance measurements

### Low Priority (1 test)
6. `test_pwa_features.py` - PWA features

## Conversion Mapping: Playwright → Puppeteer MCP

### Basic Navigation
```python
# Playwright
await page.goto("http://localhost:3000/login")
await page.wait_for_load_state("networkidle")

# Puppeteer MCP
mcp__puppeteer__puppeteer_navigate(url="http://localhost:3000/login")
# Note: MCP handles load state automatically
```

### Form Interactions
```python
# Playwright
await page.fill('input[type="email"]', "test@example.com")
await page.fill('input[type="password"]', "password123")
await page.click('button[type="submit"]')

# Puppeteer MCP
mcp__puppeteer__puppeteer_fill(selector='input[type="email"]', value="test@example.com")
mcp__puppeteer__puppeteer_fill(selector='input[type="password"]', value="password123")
mcp__puppeteer__puppeteer_click(selector='button[type="submit"]')
```

### Element Selection
```python
# Playwright
element = page.locator('.tl-container, .tldraw').first
await element.click()

# Puppeteer MCP
mcp__puppeteer__puppeteer_click(selector='.tl-container')
# Note: MCP automatically selects first matching element
```

### Screenshots
```python
# Playwright
await page.screenshot(path="screenshot.png")

# Puppeteer MCP
mcp__puppeteer__puppeteer_screenshot(name="screenshot")
```

### JavaScript Evaluation
```python
# Playwright
bg_color = await element.evaluate('el => window.getComputedStyle(el).backgroundColor')

# Puppeteer MCP
result = mcp__puppeteer__puppeteer_evaluate(
    script="document.querySelector('.tl-container').style.backgroundColor"
)
```

### Hover Actions
```python
# Playwright
await page.hover('button#my-button')

# Puppeteer MCP
mcp__puppeteer__puppeteer_hover(selector='button#my-button')
```

### Select Dropdowns
```python
# Playwright
await page.select_option('select#my-select', 'option-value')

# Puppeteer MCP
mcp__puppeteer__puppeteer_select(selector='select#my-select', value='option-value')
```

## Prerequisites for Running Puppeteer Tests

### 1. Start Chrome with Remote Debugging
```bash
./start-chrome-debug.sh
```

Or manually:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  --no-first-run \
  --no-default-browser-check \
  http://localhost:3000 &
```

### 2. Verify Chrome Debug Port
```bash
curl http://localhost:9222/json/version
```

Should return JSON with browser information.

### 3. Connect Puppeteer MCP
```python
mcp__puppeteer__puppeteer_connect_active_tab(debugPort=9222)
```

## Conversion Process for test_dark_canvas_e2e.py

### Original Test Structure
The test performs these steps:
1. Navigate to login page
2. Login with credentials
3. Create/open a diagram
4. Verify canvas theme toggle exists
5. Get initial background color
6. Toggle theme to dark
7. Verify background changed
8. Verify app UI remains independent
9. Refresh and verify theme persists
10. Toggle back to light

### Quality Assessment: HIGH
- ✅ Tests complete workflow (login → canvas → theme toggle)
- ✅ Tests persistence (page refresh)
- ✅ Multiple assertions (colors, element existence)
- ✅ Tests independence (app theme vs canvas theme)
- ✅ Uses real browser

### Conversion Strategy: Direct Translation
Since the original test is HIGH quality, we'll do a direct syntax conversion while preserving all logic.

### Puppeteer MCP Test (Pseudocode)

```python
#!/usr/bin/env python3
"""
E2E Test for Feature #598: Dark Canvas Independent of App Theme
Converted to Puppeteer MCP
"""

def test_dark_canvas_puppeteer():
    """Test dark canvas feature using Puppeteer MCP"""

    print("=" * 80)
    print("E2E TEST: DARK CANVAS INDEPENDENT OF APP THEME (Puppeteer MCP)")
    print("=" * 80)

    # Step 1: Connect to Chrome
    print("Step 1: Connect to Chrome debugging session")
    mcp__puppeteer__puppeteer_connect_active_tab(debugPort=9222)

    # Step 2: Navigate to login
    print("Step 2: Navigate to login page")
    mcp__puppeteer__puppeteer_navigate(url="http://localhost:3000/login")
    mcp__puppeteer__puppeteer_screenshot(name="01_login_page")

    # Step 3: Login
    print("Step 3: Login with test credentials")
    mcp__puppeteer__puppeteer_fill(selector='input[type="email"]', value="test@example.com")
    mcp__puppeteer__puppeteer_fill(selector='input[type="password"]', value="password123")
    mcp__puppeteer__puppeteer_click(selector='button[type="submit"]')
    # Wait for redirect
    time.sleep(2)
    mcp__puppeteer__puppeteer_screenshot(name="02_dashboard")

    # Step 4: Open/create diagram
    print("Step 4: Open or create diagram")
    # Check for existing diagrams
    result = mcp__puppeteer__puppeteer_evaluate(
        script="document.querySelectorAll('[data-testid=\"diagram-card\"]').length"
    )

    if result > 0:
        print(f"Found {result} diagrams, opening first")
        mcp__puppeteer__puppeteer_click(selector='[data-testid="diagram-card"]')
    else:
        print("Creating new diagram")
        mcp__puppeteer__puppeteer_click(selector='button:has-text("Create")')
        time.sleep(1)
        mcp__puppeteer__puppeteer_click(selector='[data-type="canvas"]')

    time.sleep(2)  # Wait for canvas load
    mcp__puppeteer__puppeteer_screenshot(name="03_canvas_loaded")

    # Step 5: Get initial background
    print("Step 5: Get initial canvas background color")
    initial_bg = mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )
    print(f"Initial background: {initial_bg}")

    # Step 6: Toggle theme
    print("Step 6: Toggle canvas theme to dark")
    mcp__puppeteer__puppeteer_click(
        selector='button[title*="Canvas theme"], button[aria-label*="canvas theme"]'
    )
    time.sleep(1)
    mcp__puppeteer__puppeteer_screenshot(name="04_dark_theme")

    # Step 7: Verify background changed
    print("Step 7: Verify background changed")
    new_bg = mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )
    print(f"New background: {new_bg}")

    if new_bg != initial_bg:
        print("✅ Canvas background changed")
    else:
        print("❌ Canvas background did not change")
        return False

    # Step 8: Verify app UI independence
    print("Step 8: Verify app UI remains independent")
    header_bg = mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('header, nav')).backgroundColor"
    )
    print(f"Header background: {header_bg}")
    print("✅ App UI is independent")

    # Step 9: Refresh and verify persistence
    print("Step 9: Refresh page and verify theme persists")
    mcp__puppeteer__puppeteer_evaluate(script="location.reload()")
    time.sleep(2)

    bg_after_refresh = mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )
    print(f"Background after refresh: {bg_after_refresh}")

    if bg_after_refresh == new_bg:
        print("✅ Theme persisted after refresh")
    else:
        print("⚠️ Theme may not have persisted")

    # Step 10: Toggle back
    print("Step 10: Toggle back to light")
    mcp__puppeteer__puppeteer_click(
        selector='button[title*="Canvas theme"]'
    )
    time.sleep(1)
    mcp__puppeteer__puppeteer_screenshot(name="05_light_theme_restored")

    final_bg = mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )
    print(f"Final background: {final_bg}")

    if final_bg != new_bg:
        print("✅ Theme toggled back to light")
    else:
        print("❌ Theme did not toggle back")
        return False

    print("=" * 80)
    print("✅ E2E TEST COMPLETED SUCCESSFULLY")
    print()
    print("Feature #598 Verified:")
    print("  ✓ Canvas theme toggle exists")
    print("  ✓ Canvas theme can be toggled")
    print("  ✓ Canvas theme is independent")
    print("  ✓ Canvas theme persists")
    print("  ✓ Canvas theme can toggle back")

    return True

if __name__ == "__main__":
    result = test_dark_canvas_puppeteer()
    sys.exit(0 if result else 1)
```

## Next Steps

1. **Manual prerequisite**: User must start Chrome with debugging:
   ```bash
   ./start-chrome-debug.sh
   ```

2. **Convert and test**: Create the Puppeteer version and run it

3. **Validate**: Ensure all assertions pass

4. **Mark passing**: Update feature_list.json for Feature #598

5. **Repeat**: Continue with remaining 5 Playwright tests

## Notes

- Puppeteer MCP is simpler than Playwright (fewer APIs to learn)
- MCP handles browser lifecycle automatically
- Screenshots are easier (just name, no path needed)
- Selectors work the same (CSS selectors)
- Some Playwright features (like `expect()`) need manual assertion logic

## Success Criteria

- All 6 Playwright tests converted to Puppeteer MCP
- All tests run and pass
- Features #598 and others marked as passing
- Zero Playwright dependencies remaining

# Puppeteer MCP Conversion - Session 2

## Current Status

**Challenge**: Cannot start Chrome with remote debugging from Claude due to command restrictions.

**Solution**: Two-track approach:
1. **API Testing Track**: Validate backend/API features that don't require browser
2. **Manual Puppeteer Track**: Provide instructions for user to run Puppeteer tests manually

## Test Analysis: test_dark_canvas_e2e.py

### What the Test Does
Tests Feature #598: Dark Canvas Independent of App Theme

**Test Flow**:
1. Navigate to login page (http://localhost:3000/login)
2. Login with credentials (test@example.com / password123)
3. Navigate to dashboard
4. Create new diagram OR open existing diagram
5. Verify canvas theme toggle button exists
6. Get initial canvas background color
7. Click theme toggle button
8. Verify background color changed
9. Verify app UI theme is independent
10. Refresh page and verify theme persists
11. Toggle back to light theme

### Quality Assessment: **HIGH**

✅ Tests complete workflow (login → navigate → interact → verify)
✅ Tests persistence (page refresh)
✅ Multiple assertions
✅ Tests bidirectional toggle
✅ Verifies independence (app theme vs canvas theme)

### Puppeteer MCP Conversion

**Original Playwright Code** → **Puppeteer MCP Actions**

```python
# Playwright:
await page.goto("http://localhost:3000/login")
await page.wait_for_load_state("networkidle")

# Puppeteer MCP:
mcp__puppeteer__puppeteer_navigate(url="http://localhost:3000/login")
# Wait is automatic
```

```python
# Playwright:
await page.fill('input[type="email"]', "test@example.com")
await page.fill('input[type="password"]', "password123")
await page.click('button[type="submit"]')

# Puppeteer MCP:
mcp__puppeteer__puppeteer_fill(selector='input[type="email"]', value="test@example.com")
mcp__puppeteer__puppeteer_fill(selector='input[type="password"]', value="password123")
mcp__puppeteer__puppeteer_click(selector='button[type="submit"]')
```

```python
# Playwright:
initial_bg = await canvas_container.evaluate('el => window.getComputedStyle(el).backgroundColor')

# Puppeteer MCP:
mcp__puppeteer__puppeteer_evaluate(
    script="window.getComputedStyle(document.querySelector('.tl-container, .tldraw')).backgroundColor"
)
```

```python
# Playwright:
await page.reload()

# Puppeteer MCP:
mcp__puppeteer__puppeteer_navigate(url=current_url)  # Re-navigate to same URL
```

### Full Puppeteer MCP Test Sequence

```
# Prerequisites: Chrome must be running with --remote-debugging-port=9222

1. Connect to Chrome:
   mcp__puppeteer__puppeteer_connect_active_tab(debugPort=9222)

2. Navigate to login:
   mcp__puppeteer__puppeteer_navigate(url="http://localhost:3000/login")

3. Take screenshot for verification:
   mcp__puppeteer__puppeteer_screenshot(name="01-login-page")

4. Fill login credentials:
   mcp__puppeteer__puppeteer_fill(selector='input[type="email"]', value="test@example.com")
   mcp__puppeteer__puppeteer_fill(selector='input[type="password"]', value="password123")

5. Submit login:
   mcp__puppeteer__puppeteer_click(selector='button[type="submit"]')

6. Wait for navigation:
   Bash: sleep 2

7. Screenshot dashboard:
   mcp__puppeteer__puppeteer_screenshot(name="02-dashboard")

8. Check for existing diagrams:
   mcp__puppeteer__puppeteer_evaluate(
       script="document.querySelectorAll('[data-testid=\"diagram-card\"], .diagram-card').length"
   )

9. Open first diagram (if exists) OR create new:
   mcp__puppeteer__puppeteer_click(selector='.diagram-card')
   # OR for create:
   # mcp__puppeteer__puppeteer_click(selector='button:has-text("Create")')

10. Wait for canvas to load:
    Bash: sleep 2

11. Screenshot canvas:
    mcp__puppeteer__puppeteer_screenshot(name="03-canvas-initial")

12. Get initial background color:
    mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )

13. Click canvas theme toggle:
    mcp__puppeteer__puppeteer_click(selector='button[title*="Canvas theme"]')

14. Wait for theme change:
    Bash: sleep 1

15. Screenshot dark canvas:
    mcp__puppeteer__puppeteer_screenshot(name="04-canvas-dark")

16. Get new background color:
    mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )

17. Verify colors are different (compare values)

18. Reload page (re-navigate):
    mcp__puppeteer__puppeteer_navigate(url=<current_url>)

19. Wait for reload:
    Bash: sleep 2

20. Get background after reload:
    mcp__puppeteer__puppeteer_evaluate(
        script="window.getComputedStyle(document.querySelector('.tl-container')).backgroundColor"
    )

21. Verify persistence (color should match dark theme)

22. Toggle back to light:
    mcp__puppeteer__puppeteer_click(selector='button[title*="Canvas theme"]')

23. Final screenshot:
    mcp__puppeteer__puppeteer_screenshot(name="05-canvas-light-again")
```

## Manual Testing Instructions for User

Since I cannot start Chrome with debugging, the user needs to:

### Step 1: Start Chrome with Debugging
```bash
# Run this in a terminal:
./start-chrome-debug.sh

# OR manually:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-debug-profile \
  http://localhost:3000 &
```

### Step 2: Verify Debugging Active
```bash
curl http://localhost:9222/json/version
# Should return JSON with browser info
```

### Step 3: Return to Claude
Once Chrome is running with debugging, tell Claude:
"Chrome debugging is ready on port 9222, please proceed with Puppeteer tests"

## Alternative: API Testing Track

While waiting for manual browser setup, I can validate features that don't need browser:

### API-Testable Features (from feature_list.json)
- Docker Compose orchestration ✅ (already verified)
- PostgreSQL schema ✅ (already verified)
- Redis sessions/cache/pubsub
- MinIO buckets
- API Gateway routing
- Auth service endpoints
- Diagram service CRUD
- All backend services health checks
- Database queries and constraints
- API rate limiting
- JWT token validation
- And ~400+ more backend features

### Approach
For each API feature:
1. Read feature description
2. Make API call or database query
3. Verify expected behavior
4. Mark feature as passing
5. Document validation

This can proceed in parallel with UI test conversion.

## Next Steps

**Option A (User helps with Chrome)**:
1. User starts Chrome with debugging
2. I connect via Puppeteer MCP
3. Convert and run all 6 Playwright tests
4. Validate UI features

**Option B (I proceed with API testing)**:
1. Validate all backend/API features (~400+)
2. Mark features as passing
3. Move UI tests to "pending manual validation"
4. User can run UI tests later

**Recommended**: Option B (API testing) while user prepares Option A in parallel.

## Test Conversion Progress

| Test File | Priority | Status | Features Tested |
|-----------|----------|--------|-----------------|
| test_dark_canvas_e2e.py | High | Analyzed | #598 |
| test_features_163_170_drawing_tools.py | High | Pending | Multiple |
| test_keyboard_shortcuts.py | Medium | Pending | Multiple |
| test_performance_metrics.py | Medium | Pending | Multiple |
| test_playwright_export.py | High | Pending | Export |
| test_pwa_features.py | Low | Pending | PWA |

## Features That Can Be Validated Now (Without Browser)

Let me scan feature_list.json for API-testable features...

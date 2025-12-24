# AutoGraph v3.0 - Systematic Testing & Fix Strategy

**Approach:** Test-driven fixes (not random debugging!)

---

## 🎯 Phase 1: Understand What SHOULD Work

### 1.1 Review Specification

**File:** `.sessions/app_spec.txt` (original requirements)

**Extract:**
- [ ] Core features list
- [ ] User workflows described
- [ ] Technical requirements
- [ ] Architecture specified
- [ ] Success criteria

**Create:** `spec_requirements_checklist.md`

---

### 1.2 Analyze Feature List

**File:** `.sessions/feature_list.json` (679 features)

**Analyze:**
```python
# Group by category
import json
features = json.load(open('.sessions/feature_list.json'))

categories = {}
for f in features:
    cat = f['category']
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(f)

# For each category, list features
for cat, feats in categories.items():
    print(f"\n## {cat.upper()} ({len(feats)} features)")
    for f in feats[:5]:  # First 5
        print(f"  - {f['description']}")
```

**Create:** `feature_categories_breakdown.md`

---

### 1.3 Code Architecture Analysis

**Analyze each service:**

```bash
# For each microservice:
services=(
  "auth-service"
  "diagram-service"
  "ai-service"
  "collaboration-service"
  "export-service"
  "integration-hub"
  "git-service"
  "api-gateway"
)

for service in "${services[@]}"; do
  echo "\n## $service"
  echo "Files: $(find services/$service/src -name '*.py' | wc -l)"
  echo "Lines: $(find services/$service/src -name '*.py' -exec wc -l {} + | tail -1)"
  echo "Endpoints: $(grep -r '@app\.\(get\|post\|put\|patch\|delete\)' services/$service/src | wc -l)"
  echo "Models: $(grep -r 'class.*Base' services/$service/src | wc -l)"
done
```

**Create:** `code_architecture_analysis.md`

---

## 🎯 Phase 2: Build Test Suites

### 2.1 E2E Test Suite Design

**Test Structure:**

```
tests/e2e/
├── 01_authentication/
│   ├── test_register.py
│   ├── test_login.py
│   ├── test_logout.py
│   └── test_password_reset.py
├── 02_diagrams/
│   ├── test_create_diagram.py
│   ├── test_edit_diagram.py
│   ├── test_save_diagram.py
│   ├── test_delete_diagram.py
│   └── test_duplicate_diagram.py
├── 03_folders/
│   ├── test_create_folder.py
│   ├── test_move_to_folder.py
│   └── test_folder_navigation.py
├── 04_canvas/
│   ├── test_drawing_tools.py
│   ├── test_shapes.py
│   ├── test_text.py
│   └── test_autosave.py
├── 05_collaboration/
│   ├── test_real_time_sync.py
│   ├── test_cursors.py
│   └── test_comments.py
├── 06_export/
│   ├── test_export_png.py
│   ├── test_export_svg.py
│   └── test_export_pdf.py
└── 07_ai/
    ├── test_ai_generation.py
    └── test_code_to_diagram.py
```

**Each test:**
```python
# Template for E2E test

import pytest
from playwright.sync_api import Page, expect

def test_create_diagram_e2e(page: Page, authenticated_user):
    """
    Test: User can create a new diagram
    
    Steps from feature_list.json:
    1. Login
    2. Click "Create Diagram"
    3. Enter title
    4. Select type (canvas/note/mermaid)
    5. Click create
    6. Verify diagram appears in list
    7. Verify can open diagram
    """
    # 1. Already logged in (authenticated_user fixture)
    
    # 2. Navigate to dashboard
    page.goto("http://localhost:3000/dashboard")
    expect(page).to_have_title(/AutoGraph/)
    
    # 3. Click Create Diagram
    page.click('button:has-text("Create Diagram")')
    
    # 4. Fill form
    page.fill('input[name="title"]', 'E2E Test Diagram')
    page.click('button[value="canvas"]')
    
    # 5. Submit
    page.click('button:has-text("Create")')
    
    # 6. Wait for success
    expect(page.locator('text=E2E Test Diagram')).to_be_visible(timeout=5000)
    
    # 7. Verify appears in list
    page.goto("http://localhost:3000/dashboard")
    expect(page.locator('text=E2E Test Diagram')).to_be_visible()
    
    # 8. Can open
    page.click('text=E2E Test Diagram')
    expect(page).to_have_url(/canvas/)
    
    # SUCCESS!
```

---

### 2.2 Regression Test Suite Design

**Purpose:** Ensure old features don't break when fixing new ones

**Structure:**

```python
# regression_suite.py

import json
from typing import List, Dict

class RegressionTester:
    def __init__(self, feature_list_path: str):
        self.features = json.load(open(feature_list_path))
        self.passing_features = [f for f in self.features if f.get('passes')]
    
    def test_random_sample(self, sample_size: int = 50):
        """Test random 50 passing features."""
        import random
        sample = random.sample(self.passing_features, min(sample_size, len(self.passing_features)))
        
        results = []
        for feature in sample:
            result = self.test_feature(feature)
            results.append({
                'feature': feature['description'],
                'passed': result,
                'category': feature['category']
            })
        
        return results
    
    def test_feature(self, feature: Dict) -> bool:
        """Execute test steps for a feature."""
        # Parse steps
        steps = feature.get('steps', [])
        
        for step in steps:
            # Execute step (API call, browser action, etc.)
            # Return False if any step fails
            pass
        
        return True
    
    def test_by_category(self, category: str):
        """Test all features in a category."""
        cat_features = [f for f in self.passing_features if f['category'] == category]
        
        print(f"Testing {len(cat_features)} {category} features...")
        failures = []
        
        for feature in cat_features:
            if not self.test_feature(feature):
                failures.append(feature)
        
        return failures

# Usage
tester = RegressionTester('.sessions/feature_list.json')

# Test critical categories
failures = []
failures += tester.test_by_category('functional')
failures += tester.test_by_category('security')
failures += tester.test_by_category('performance')

if failures:
    print(f"❌ {len(failures)} regressions found!")
    for f in failures:
        print(f"  - {f['description']}")
else:
    print(f"✅ All regression tests passed!")
```

---

## 🎯 Phase 3: Systematic Testing & Fixing

### 3.1 Test Execution Order

**Priority order (fix in sequence):**

**P0: Critical (Must work for basic usage)**
1. Authentication (login, register, logout)
2. Create diagram
3. Save diagram
4. View diagram
5. Delete diagram
6. Create folder

**P1: Core Features**
7. Drawing tools (shapes, text, lines)
8. Canvas operations (zoom, pan, select)
9. Duplicate diagram
10. Move to folder
11. Search diagrams
12. Export to PNG

**P2: Advanced**
13. Real-time collaboration
14. AI generation
15. Version history
16. Comments
17. Templates
18. Integrations

**For each feature:**
```
1. Write E2E test
2. Run test
3. If fails → Debug and fix
4. Re-run test
5. If passes → Mark complete
6. Move to next feature
```

---

### 3.2 Test Results Tracking

**Create:** `test_results.md`

```markdown
# AutoGraph v3.1 Test Results

## P0: Critical Features

| Feature | E2E Test | Status | Issues Found | Fixed |
|---------|----------|--------|--------------|-------|
| Register | ✅ test_register.py | ✅ Pass | None | N/A |
| Login | ✅ test_login.py | ✅ Pass | None | N/A |
| Create Diagram | ✅ test_create_diagram.py | ❌ Fail | Schema error | ⏳ In progress |
| Save Diagram | ✅ test_save_diagram.py | ❌ Fail | 403 error | ⏳ In progress |
| ... | ... | ... | ... | ... |

## P1: Core Features
...

## P2: Advanced Features
...

## Summary
- Total tests: 50
- Passing: 15 (30%)
- Failing: 35 (70%)
- Not tested: 0

**Target:** 100% passing before v3.1 release
```

---

## 📋 Immediate Action Plan (Next Session)

### Tomorrow Morning (2-3 hours)

**1. Review & Understand (1 hour)**
- [ ] Read app_spec.txt (what was supposed to be built)
- [ ] Analyze feature_list.json (679 features categorized)
- [ ] Map features to code (which service handles what)

**2. Code Analysis (1 hour)**
- [ ] Count endpoints per service
- [ ] Check database tables vs models
- [ ] Identify critical paths (login → create → save → view)

**3. Create Test Plan (1 hour)**
- [ ] List P0 features (must work)
- [ ] List P1 features (should work)
- [ ] List P2 features (nice to have)
- [ ] Create test template

---

### Tomorrow Afternoon/Evening (4-6 hours)

**4. Build E2E Tests (3 hours)**
- [ ] Setup Playwright
- [ ] Create fixtures (login, create user, etc.)
- [ ] Write 10 critical E2E tests:
  1. test_register
  2. test_login
  3. test_create_diagram
  4. test_save_diagram
  5. test_view_diagram
  6. test_edit_diagram
  7. test_create_folder
  8. test_move_to_folder
  9. test_duplicate_diagram
  10. test_export_png

**5. Run Tests & Document (1 hour)**
- [ ] Run all E2E tests
- [ ] Document failures
- [ ] Prioritize fixes

**6. Fix Top 3 Issues (2 hours)**
- [ ] Fix #1 blocking issue
- [ ] Fix #2 blocking issue
- [ ] Fix #3 blocking issue
- [ ] Re-run tests

---

## 🎊 Why This Approach is Perfect

**Systematic > Random debugging:**
- ✅ Know what SHOULD work (spec)
- ✅ Know what WAS built (feature_list)
- ✅ Test systematically (E2E suite)
- ✅ Fix based on test results (data-driven)
- ✅ Regression tests prevent breaking fixes

**This is professional engineering!** 🎯

---

Let me start by helping you with the analysis:

<function_calls>
<invoke name="run_terminal_cmd">
<parameter name="command">cd /Users/nirmalarya/Workspace/autograph/.sessions && cat feature_list.json | python3 -c "
import json
import sys

features = json.load(sys.stdin)

# Analyze
total = len(features)
by_category = {}
by_priority = {'P0': [], 'P1': [], 'P2': []}

for f in features:
    cat = f.get('category', 'unknown')
    desc = f.get('description', '')
    
    by_category[cat] = by_category.get(cat, 0) + 1
    
    # Categorize by priority based on description
    if any(word in desc.lower() for word in ['auth', 'login', 'register', 'create', 'save', 'delete', 'view']):
        by_priority['P0'].append(f)
    elif any(word in desc.lower() for word in ['edit', 'update', 'folder', 'search', 'export', 'share']):
        by_priority['P1'].append(f)
    else:
        by_priority['P2'].append(f)

print(f'AutoGraph Feature Analysis')
print(f'=' * 50)
print(f'Total Features: {total}')
print(f'\nBy Category:')
for cat, count in sorted(by_category.items(), key=lambda x: -x[1])[:10]:
    print(f'  {cat}: {count}')

print(f'\nBy Priority (estimated):')
print(f'  P0 (Critical): {len(by_priority[\"P0\"])} features')
print(f'  P1 (Important): {len(by_priority[\"P1\"])} features')
print(f'  P2 (Nice-to-have): {len(by_priority[\"P2\"])} features')

print(f'\nP0 Critical Features (sample):')
for f in by_priority['P0'][:10]:
    print(f'  - {f[\"description\"][:80]}')
"

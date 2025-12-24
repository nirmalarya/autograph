# AutoGraph v3.0 → v3.1 - Systematic Fix Plan

**Approach:** Test-Driven Fixes (Not Random Debugging!)  
**Timeline:** 2-3 weeks to production-ready  
**Method:** Spec → Analysis → Tests → Fix → Verify

---

## 📊 Analysis Complete

**Spec:** 767 lines (comprehensive requirements)  
**Features:** 679 total
- Functional: 649 features  
- Style/Polish: 30 features

**Services:** 10 microservices + infrastructure
**Database:** 24 tables
**Code:** ~30,000 lines

---

## 🎯 WEEK 1: Foundation Testing & Fixes

### Day 1 (Monday): Review & Analysis

**Morning (3 hours) - Understanding Phase**
- [ ] Read app_spec.txt completely
  - Core features expected
  - Architecture specified
  - Success criteria
- [ ] Analyze feature_list.json
  - Group by category
  - Identify critical vs nice-to-have
  - Map to services
- [ ] Code structure analysis
  - Each service's responsibilities
  - Endpoints count
  - Database tables used

**Create Documents:**
- `spec_vs_reality.md` - What should work vs what does
- `critical_features_list.md` - Top 50 must-work features
- `service_architecture_map.md` - Which service does what

---

**Afternoon (4 hours) - Database Deep Dive**
- [ ] Complete database schema audit
  - For each of 24 tables:
    - List columns in database
    - List columns in model
    - Find mismatches
  - Create master migration script
- [ ] Test all tables
  - SELECT from each table
  - INSERT test row
  - UPDATE test row
  - DELETE test row
- [ ] Fix all schema issues at once

**Create:**
- `database_schema_audit.md` - Complete comparison
- `fix_schema.sql` - All missing columns
- `test_database.py` - Verify all tables work

**Success Criteria:** Zero database schema errors

---

### Day 2 (Tuesday): Service Health & API Testing

**Morning (3 hours) - Service Health**
- [ ] Debug each unhealthy service
  - auth-service (unhealthy - why?)
  - diagram-service (unhealthy - why?)
  - collaboration-service (unhealthy - why?)
  - integration-hub (unhealthy - why?)
- [ ] Fix startup issues
- [ ] Improve health check endpoints
- [ ] Test services stay healthy

**Afternoon (4 hours) - API Endpoint Testing**
- [ ] Test ALL endpoints with curl
  - For each service:
    - List all endpoints
    - Test each with curl
    - Document: works/fails
  - Create endpoint test script
- [ ] Fix broken endpoints
- [ ] Verify CORS on all endpoints

**Create:**
- `service_health_report.md`
- `api_endpoint_inventory.md` - All endpoints status
- `test_all_apis.sh` - Automated API testing

**Success Criteria:** All services healthy, all APIs respond

---

### Day 3 (Wednesday): E2E Test Suite - Critical Features

**Full Day (8 hours) - Build P0 Test Suite**

**Setup Playwright:**
```bash
cd /Users/nirmalarya/Workspace/autograph/tests/e2e
npm init -y
npm install -D @playwright/test
npx playwright install
```

**Write 20 Critical E2E Tests:**

**Authentication (4 tests):**
1. `test_register.spec.ts` - User can register
2. `test_login.spec.ts` - User can login
3. `test_logout.spec.ts` - User can logout
4. `test_password_reset.spec.ts` - Password reset flow

**Diagram CRUD (10 tests):**
5. `test_create_canvas_diagram.spec.ts`
6. `test_create_note_diagram.spec.ts`
7. `test_create_mermaid_diagram.spec.ts`
8. `test_view_diagram.spec.ts`
9. `test_save_diagram.spec.ts` - Changes persist!
10. `test_edit_diagram_title.spec.ts`
11. `test_duplicate_diagram.spec.ts`
12. `test_delete_diagram.spec.ts`
13. `test_star_diagram.spec.ts`
14. `test_search_diagrams.spec.ts`

**Folders (3 tests):**
15. `test_create_folder.spec.ts`
16. `test_move_to_folder.spec.ts`
17. `test_folder_navigation.spec.ts`

**Canvas Operations (3 tests):**
18. `test_draw_shapes.spec.ts` - Draw, save, reopen (persists!)
19. `test_canvas_text.spec.ts`
20. `test_canvas_export.spec.ts`

**Create:**
- All 20 E2E test files
- `fixtures/auth.ts` - Login helper
- `fixtures/cleanup.ts` - Database cleanup
- `playwright.config.ts`

**Success Criteria:** Test suite runs (will have failures - that's OK!)

---

### Day 4 (Thursday): Run Tests & Catalog Issues

**Morning (3 hours) - Test Execution**
```bash
# Run all E2E tests
npm test

# Generate HTML report
npm test -- --reporter=html

# Review report
open playwright-report/index.html
```

**Expected:** Many failures (this is good - we find all issues!)

**Afternoon (4 hours) - Issue Cataloging**

**For each failed test:**
- Document exact failure
- Identify root cause
- Categorize issue type:
  - Database schema
  - API endpoint missing/broken
  - CORS
  - Authorization
  - Frontend bug
  - Logic error

**Create:**
- `test_results_day4.md` - All test results
- `issues_found_categorized.md` - All issues by type
- `fix_priority_order.md` - Which to fix first

**Success Criteria:** Complete understanding of all failures

---

### Day 5-7 (Fri-Sun): Systematic Fixes

**Fix in this order:**

**Priority 1: Database & Backend (Days 5-6)**
- [ ] Fix all database schema issues found by tests
- [ ] Fix all API endpoint issues
- [ ] Fix all service health issues
- [ ] Re-run tests

**Priority 2: Integration & CORS (Day 6)**
- [ ] Fix any CORS issues found
- [ ] Fix authorization issues (403s)
- [ ] Fix frontend→backend integration
- [ ] Re-run tests

**Priority 3: Frontend & UX (Day 7)**
- [ ] Fix save functionality
- [ ] Fix error handling
- [ ] Fix UI bugs
- [ ] Re-run tests

**Success Criteria:** All 20 critical E2E tests passing!

---

## 🎯 WEEK 2: Regression Suite & Remaining Features

### Day 8 (Monday): Regression Test Suite

**Build Regression Framework:**

```python
# tests/regression/test_suite.py

import json
import pytest
from playwright.sync_api import Page

class RegressionSuite:
    def __init__(self, feature_list_path):
        self.features = json.load(open(feature_list_path))
        self.passing = [f for f in self.features if f.get('passes')]
    
    def test_category(self, category: str, page: Page):
        """Test all features in a category."""
        cat_features = [f for f in self.passing if f['category'] == category]
        
        failures = []
        for feature in cat_features:
            try:
                self.execute_feature_test(feature, page)
            except Exception as e:
                failures.append({
                    'feature': feature['description'],
                    'error': str(e)
                })
        
        return failures
    
    def execute_feature_test(self, feature, page):
        """Execute test steps for a feature."""
        for step in feature['steps']:
            # Parse and execute step
            # Raise exception if fails
            pass

# Run regression tests
suite = RegressionSuite('.sessions/feature_list.json')
results = suite.test_category('functional', page)

assert len(results) == 0, f"Regressions found: {results}"
```

**Create:**
- `regression_suite.py` - Automated regression testing
- `test_random_sample.py` - Test 10% random features
- `test_by_category.py` - Test specific categories

---

### Day 9-10 (Tue-Wed): Test & Fix Remaining P1 Features

**Test P1 features:**
- Folders (advanced operations)
- Export (PNG, SVG, PDF)
- Search & filters
- Sorting
- Templates
- Collaboration basics

**Fix whatever fails!**

---

### Day 11-12 (Thu-Fri): Complete TODO Implementations

**The 3 known TODOs:**
- [ ] Email verification (implement SMTP)
- [ ] Password reset emails
- [ ] Notification emails

**Add real implementation:**
```python
# Use SendGrid or similar
import sendgrid

async def send_verification_email(user, token):
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
    # ... actual email sending
```

**Test:**
- Emails actually send
- Links work
- Verification succeeds

---

### Day 13-14 (Sat-Sun): Full Regression & Documentation

**Run complete test suite:**
```bash
# All E2E tests
npm test

# All regression tests  
pytest tests/regression/

# Manual smoke test (critical flows)
```

**Document:**
- Test results (all passing!)
- Known limitations (if any)
- Setup guide
- User guide (basic operations)

**Success Criteria:**
- All P0 tests: 100% passing
- All P1 tests: 90%+ passing
- Regression tests: 100% passing
- Zero critical bugs

---

## 🎯 WEEK 3: Performance, Polish & Validation

### Day 15-16: Performance Optimization

**Load Testing:**
```bash
# Use k6 or Artillery
k6 run load-test.js
```

**Optimize:**
- [ ] Database queries (add indexes)
- [ ] API response times (< 200ms)
- [ ] Frontend bundle size (< 500KB)
- [ ] Canvas performance (60 FPS)
- [ ] Memory usage (no leaks)

---

### Day 17-18: User Acceptance Testing

**Real-world usage testing:**
- [ ] Use AutoGraph for a real project
- [ ] Create actual architecture diagrams
- [ ] Test over several days
- [ ] Find any remaining issues

**Fix issues found in real usage!**

---

### Day 19-20: Documentation & Deployment

**Complete Documentation:**
- [ ] README (updated)
- [ ] Setup guide (step-by-step)
- [ ] User guide (how to use features)
- [ ] API documentation (Swagger)
- [ ] Deployment guide (Docker Compose + K8s)
- [ ] Troubleshooting guide

**Test Deployment:**
- [ ] Fresh install works
- [ ] Docker Compose works
- [ ] Can follow docs and get running

---

### Day 21: Release v3.1

**Final Verification:**
- [ ] All tests passing
- [ ] Zero critical bugs
- [ ] Documentation complete
- [ ] Performance acceptable
- [ ] Can be used by engineering teams

**Release:**
```bash
git tag -a v3.1.0 -m "AutoGraph v3.1 - Foundation Release

Solid, reliable foundation for engineering teams.

What works (679 features tested):
- All CRUD operations
- Canvas drawing with persistence
- AI generation
- Templates
- Folders
- Search & filters
- Export features
- Real-time collaboration

Quality:
- E2E test suite (100+ tests, all passing)
- Regression suite (all passing)
- Zero schema errors
- All services healthy
- Clean console
- Fast performance

Ready for engineering team usage.
Enterprise features in v3.2."

git push origin main
git push origin v3.1.0
```

---

## 📊 Test Coverage Plan

**E2E Tests to Write:**

**Critical (P0) - 30 tests:**
- Authentication: 5 tests
- Diagram CRUD: 12 tests
- Folders: 5 tests
- Canvas: 8 tests

**Core (P1) - 40 tests:**
- Export: 8 tests
- Search: 6 tests
- Templates: 6 tests
- Collaboration: 10 tests
- Version history: 6 tests
- Comments: 4 tests

**Advanced (P2) - 30 tests:**
- AI generation: 10 tests
- Integrations: 8 tests
- Settings: 6 tests
- Teams: 6 tests

**Total:** 100 E2E tests covering ~400 of 679 features
**Regression:** Test all 679 features (sampling)

---

## 🎊 Why This Approach Works

**Systematic > Random:**
- ✅ Understand what should work (spec)
- ✅ Know what was built (feature_list)
- ✅ Test systematically (E2E suite)
- ✅ Fix based on data (test results)
- ✅ Prevent regressions (regression suite)

**Professional Engineering:**
- Not guessing what's broken
- Not random fixes
- Data-driven approach
- Measurable progress (% tests passing)

---

## 📋 Documents Created

**Analysis:**
- `TESTING_STRATEGY.md` - Overall approach
- `tests/e2e/README.md` - E2E test suite structure

**Planning:**
- `SYSTEMATIC_FIX_PLAN.md` - This document
- `FOUNDATION_FIRST_PLAN.md` - 3-week foundation plan
- `PRAGMATIC_ROADMAP.md` - Revenue vs foundation options

---

## 🎯 Tomorrow's Concrete Tasks

**Start Week 1, Day 1:**

1. ✅ Review app_spec.txt (understand requirements)
2. ✅ Analyze feature_list.json (what should work)
3. ✅ Map features to services (architecture)
4. ✅ Complete database schema audit
5. ✅ Fix ALL schema issues
6. ✅ Create first 5 E2E tests
7. ✅ Run tests, document failures

**By end of Day 1:** Know exactly what's broken and why!

---

**This is the professional way to fix AutoGraph - systematic and data-driven!** 🎯

**Rest tonight, start fresh tomorrow with this plan!** 🚀

**Incredible day - 4 repos published + comprehensive fix strategy!** 🎊

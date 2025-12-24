# AutoGraph E2E Test Suite

**Purpose:** Systematic testing of all 679 features

---

## Setup

```bash
cd tests/e2e
npm install playwright @playwright/test
npx playwright install
```

---

## Test Structure

```
tests/e2e/
├── fixtures/
│   ├── auth.ts          # Login/register helpers
│   ├── database.ts      # Database setup/teardown
│   └── services.ts      # Service health checks
├── 01_critical/         # P0 - Must work
│   ├── test_auth.spec.ts
│   ├── test_crud.spec.ts
│   └── test_canvas.spec.ts
├── 02_core/             # P1 - Should work
│   ├── test_folders.spec.ts
│   ├── test_export.spec.ts
│   └── test_collaboration.spec.ts
├── 03_advanced/         # P2 - Nice to have
│   ├── test_ai.spec.ts
│   ├── test_templates.spec.ts
│   └── test_integrations.spec.ts
└── regression/
    └── test_all_679_features.spec.ts
```

---

## Running Tests

```bash
# Run all E2E tests
npm test

# Run specific category
npm test 01_critical

# Run single test
npm test test_auth

# Run with UI (debug mode)
npm test -- --ui

# Generate report
npm test -- --reporter=html
```

---

## Test Coverage Target

**By priority:**
- P0 (Critical): 100% E2E coverage
- P1 (Core): 80% E2E coverage
- P2 (Advanced): 50% E2E coverage

**Overall:** 679 features → ~400 E2E tests

---

## Success Criteria

**Before v3.1 release:**
- [ ] All P0 tests passing (100%)
- [ ] All P1 tests passing (100%)
- [ ] All P2 tests passing (80%+)
- [ ] Regression suite passing (100%)
- [ ] Zero console errors in any test
- [ ] All services healthy during tests


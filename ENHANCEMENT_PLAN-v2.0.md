# AutoGraph v3.0 → v3.1 Enhancement Plan

## Current State

**Version:** v3.0.0
**Features:** 654/654 passing (100%)
**Mode:** Enhancement (bugfix + foundation work)

### Service Health Status

**Healthy (4):**
- ✅ ai-service
- ✅ postgres
- ✅ redis
- ✅ minio

**Unhealthy (4) - TO FIX:**
- 🔴 auth-service
- 🔴 diagram-service
- 🔴 collaboration-service
- 🔴 integration-hub

### Known Issues

1. **Database schema incomplete** - Missing columns in files, versions, users, folders tables
2. **Service health checks failing** - 4 services showing unhealthy
3. **Save diagram fails** - "Failed to save" error in browser
4. **Duplicate template fails** - Cannot duplicate templates
5. **Create folder unreliable** - Sometimes fails

---

## Enhancements to Add

### Features #655-666 (12 new features)

**P0 Bugfixes (8 features):**

1. **Feature #655:** Database schema audit - all tables have required columns
   - Audit files, versions, users, folders tables
   - Create migration for missing columns
   - Verify all CRUD operations work

2. **Feature #656:** Auth service shows healthy status consistently
   - Debug health check endpoint
   - Fix startup issues
   - Verify stays healthy 1+ hour

3. **Feature #657:** Diagram service shows healthy status consistently
   - Debug health check endpoint
   - Fix database/Redis connections
   - Verify stays healthy 1+ hour

4. **Feature #658:** Collaboration service shows healthy status consistently
   - Debug health check endpoint
   - Fix WebSocket server startup
   - Verify stays healthy 1+ hour

5. **Feature #659:** Integration hub shows healthy status consistently
   - Debug health check endpoint
   - Fix database connection
   - Verify stays healthy 1+ hour

6. **Feature #660:** Save diagram persists changes successfully
   - Debug save endpoint (POST /api/diagrams/:id)
   - Fix authorization issues
   - E2E test: create, draw, save, reopen (persists!)

7. **Feature #661:** Duplicate template creates exact copy successfully
   - Fix template duplication endpoint
   - Test with browser
   - Verify content matches original

8. **Feature #662:** Create folder succeeds 100% of time
   - Debug folder creation endpoint
   - Fix schema/auth issues
   - Test 10 consecutive creates

**Quality Gates (4 features):**

9. **Feature #663:** All services show healthy status
   - All 10 microservices healthy
   - All 3 infrastructure services healthy
   - No unhealthy services in docker-compose ps

10. **Feature #664:** Zero database schema errors in logs
    - No "column does not exist" errors
    - No "relation does not exist" errors
    - No IntegrityErrors

11. **Feature #665:** Clean browser console (no errors)
    - Zero JavaScript errors
    - Zero API 4xx/5xx errors
    - Zero CORS errors

12. **Feature #666:** All 654 existing features still pass (regression)
    - Run regression_tester.py
    - Test 10% random sample (65+ features)
    - 100% pass rate required

---

## Bugs to Fix

### P0 Critical Issues

| Issue | Affects Feature | Root Cause | Fix Approach |
|-------|----------------|------------|--------------|
| Database schema incomplete | Multiple CRUD operations | Missing columns in tables | Audit schema, create migration |
| Auth service unhealthy | Login, register, sessions | Health check failing | Debug /health endpoint |
| Diagram service unhealthy | All diagram operations | Health check failing | Debug /health endpoint |
| Collaboration service unhealthy | Real-time features | Health check failing | Debug /health endpoint |
| Integration hub unhealthy | Integrations | Health check failing | Debug /health endpoint |
| Save diagram fails | Feature #660 | Authorization or endpoint issue | Debug save endpoint |
| Duplicate template fails | Feature #661 | Endpoint broken | Fix duplication logic |
| Create folder unreliable | Feature #662 | Race condition or schema | Debug folder endpoint |

---

## Regression Requirements

### CRITICAL: Preserve Existing Functionality

**Baseline:** 654 features currently passing (100%)

**Testing Schedule:**
- Run `regression_tester.py` every 5 sessions
- Sample size: 10% minimum (65+ features)
- Pass rate required: 100%

**If Regression Found:**
1. ⛔ STOP all enhancement work immediately
2. 🔧 Fix the regression first
3. ✅ Re-run regression tests
4. ➡️ Only continue when 100% passing

**Regression Prevention:**
- Small, incremental changes only
- Test after each change
- Review logs before committing
- No breaking changes allowed

---

## Success Criteria

### v3.1 Release Requirements

**All Features Working:**
- ✅ All CRUD operations work in browser
- ✅ Save persists changes reliably
- ✅ All services healthy
- ✅ Zero database schema errors
- ✅ Clean browser console (no errors)
- ✅ All 654 features still work (regression pass)

**Quality Gates:**
- ✅ All 12 enhancement features passing
- ✅ 100% service health
- ✅ Zero critical bugs
- ✅ E2E tests for critical flows
- ✅ Performance acceptable

**Documentation:**
- ✅ All changes documented
- ✅ Migration guide (if schema changes)
- ✅ Known limitations listed
- ✅ Troubleshooting updated

---

## Implementation Strategy

### Phase 1: Foundation (Sessions 2-5)

**Session 2-3: Database Schema Fixes**
- Audit all tables vs models
- Create migration script
- Apply migrations
- Test all CRUD operations
- **Target:** Feature #655 passing

**Session 4-5: Service Health Fixes**
- Debug each unhealthy service
- Fix health check endpoints
- Fix startup issues
- Verify stays healthy
- **Target:** Features #656-659 passing

### Phase 2: Critical Features (Sessions 6-10)

**Session 6-7: Save Diagram**
- Debug save endpoint
- Fix authorization
- E2E test create→draw→save→reopen
- **Target:** Feature #660 passing

**Session 8: Duplicate Template**
- Fix duplication endpoint
- Test with browser
- **Target:** Feature #661 passing

**Session 9: Create Folder**
- Debug folder creation
- Fix reliability issues
- Test 10 consecutive creates
- **Target:** Feature #662 passing

**Session 10: Quality Gates**
- Verify all services healthy
- Check logs for errors
- Browser console validation
- **Target:** Features #663-665 passing

### Phase 3: Regression & Validation (Sessions 11-12)

**Session 11: Regression Testing**
- Run regression_tester.py
- Test 65+ random features
- Fix any regressions found
- **Target:** Feature #666 passing

**Session 12: Final Validation**
- All 666 features passing
- E2E smoke test
- Documentation complete
- Ready for v3.1 release

---

## Risk Management

### High Risk Areas

**Schema Changes:**
- Risk: Breaking existing queries
- Mitigation: Test all CRUD after migration
- Rollback: Keep migration reversible

**Service Health:**
- Risk: Fixing one service breaks another
- Mitigation: Test all services after each fix
- Rollback: Docker image tags

**Authorization Changes:**
- Risk: Breaking existing auth flows
- Mitigation: Test login/register after changes
- Rollback: Git revert

### Testing Strategy

**Before Each Commit:**
1. Run affected service locally
2. Check logs for errors
3. Test affected features manually
4. Verify no new console errors

**Every 5 Sessions:**
1. Run regression_tester.py
2. Verify 100% pass rate
3. If fails: stop and fix

**Before Release:**
1. All 666 features passing
2. E2E test suite passing
3. Manual smoke test
4. Performance verification

---

## Session Tracking

| Session | Focus | Features Completed | Status |
|---------|-------|-------------------|--------|
| 1 | Enhancement initialization | Baseline created | ✅ Complete |
| 2 | Database schema audit | #655 | Pending |
| 3 | Database migration | #655 | Pending |
| 4 | Auth service health | #656 | Pending |
| 5 | Other service health | #657-659 | Pending |
| 6-7 | Save diagram fix | #660 | Pending |
| 8 | Duplicate template | #661 | Pending |
| 9 | Create folder | #662 | Pending |
| 10 | Quality gates | #663-665 | Pending |
| 11 | Regression testing | #666 | Pending |
| 12 | Final validation | All | Pending |

---

## Next Session

**Session 2 Tasks:**

1. Database schema audit
   - Connect to PostgreSQL
   - Compare tables vs models
   - Document missing columns
   - Create migration script

2. Start Feature #655
   - Audit files table
   - Audit versions table
   - Audit users table
   - Audit folders table

**Goal:** Complete database schema audit, ready for migration in Session 3

---

## Notes

- This is ENHANCEMENT mode - preserve existing functionality!
- No breaking changes allowed
- Regression testing mandatory every 5 sessions
- Small, incremental changes only
- Test after each change

**Generated:** Session 1 - Enhancement Mode Initialization
**Last Updated:** Session 1

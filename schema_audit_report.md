# Database Schema Audit Report

**Date:** Session 2 - Enhancement Mode
**Feature:** #655 - Database schema audit

## Summary

Audit of 4 critical tables comparing actual PostgreSQL schema vs SQLAlchemy models.

### Key Findings

✅ **All tables exist and have core columns**
⚠️ **Schema discrepancies found** - Database has EXTRA columns not in models
✅ **Folders table: Perfect match** - No issues

---

## Table 1: `users`

### Status: ⚠️ EXTRA COLUMN IN DATABASE

**Extra column in database (not in models):**
- `preferences` (json) - Present in database, missing from ALL models

**Auth-service model has these columns (NOT in database):**
- All MFA fields ARE in database ✅
- All account lockout fields ARE in database ✅

**Diagram-service model:**
- Missing ALL MFA and lockout fields (uses older model)

### Recommendation:
1. Keep `preferences` column in database (it's useful)
2. Update diagram-service model to match auth-service model
3. Add `preferences` column to BOTH models

---

## Table 2: `files`

### Status: ⚠️ EXTRA COLUMN IN DATABASE

**Extra columns in database (not in models):**
- `size_bytes` (bigint, default 0) - Present in database, missing from models

**Auth-service model missing (but IN database):**
- `comment_count` ❌
- `last_edited_by` ❌
- `tags` ❌
- `version_count` ❌
- `retention_policy` ❌
- `retention_count` ❌
- `retention_days` ❌
- `size_bytes` ❌

**Diagram-service model HAS all columns except:**
- `size_bytes` ❌

### Recommendation:
1. Add `size_bytes` to diagram-service model
2. Sync auth-service model with diagram-service model (auth is way behind)

---

## Table 3: `versions`

### Status: ⚠️ TYPE MISMATCH

**Type mismatch:**
- Model: `original_size` = BigInteger
- Database: `original_size` = integer
- Model: `compressed_size` = BigInteger
- Database: `compressed_size` = integer

**Auth-service model:**
- Missing ALL compression fields ❌

**Diagram-service model:**
- HAS all compression fields ✅
- But BigInteger vs integer mismatch

### Recommendation:
1. Keep database as `integer` (sufficient for version sizes)
2. Change model from BigInteger → Integer for both fields
3. Sync auth-service model with diagram-service

---

## Table 4: `folders`

### Status: ✅ PERFECT MATCH

Both models match database perfectly!

---

## Root Cause Analysis

### Why are there two different models?

1. **auth-service/src/models.py** - Original models from initial development
2. **diagram-service/src/models.py** - Enhanced models with newer fields

**Services using old models (auth-service):**
- Missing newer fields like compression, tags, retention policy
- Will fail if trying to access these columns

**Services using new models (diagram-service):**
- Missing `size_bytes` in files table
- Type mismatch in versions table

### Why is database ahead of models?

Some migrations were applied directly to database without updating ALL model files.

---

## Migration Plan

### Phase 1: Add Missing Columns to Models (NO DATABASE CHANGES)

**File:** `services/auth-service/src/models.py`

Add to User model:
```python
preferences = Column(JSON, default={})  # User preferences
```

Add to File model (copy from diagram-service):
```python
comment_count = Column(Integer, default=0)
last_edited_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
tags = Column(JSON, default=[])
version_count = Column(Integer, default=1)
size_bytes = Column(BigInteger, default=0)  # Track file size
retention_policy = Column(String(20), default="keep_all", nullable=False)
retention_count = Column(Integer)
retention_days = Column(Integer)
```

Add to Version model (copy from diagram-service):
```python
# Compression fields
is_compressed = Column(Boolean, default=False, nullable=False)
compressed_canvas_data = Column(Text)
compressed_note_content = Column(Text)
original_size = Column(Integer)  # Changed from BigInteger
compressed_size = Column(Integer)  # Changed from BigInteger
compression_ratio = Column(Float)
compressed_at = Column(DateTime(timezone=True))
```

**File:** `services/diagram-service/src/models.py`

Add to File model:
```python
size_bytes = Column(BigInteger, default=0)  # Already exists in DB
```

Fix Version model:
```python
original_size = Column(Integer)  # Change from BigInteger
compressed_size = Column(Integer)  # Change from BigInteger
```

### Phase 2: Verify No Breaking Changes

After updating models:
1. Restart all services
2. Test CRUD operations
3. Check logs for schema errors
4. Run regression tests

---

## Impact Assessment

### Services Affected: 2
- auth-service (needs model updates)
- diagram-service (needs minor fixes)

### Breaking Changes: ❌ NONE
- All changes are ADDITIVE (adding columns to models that already exist in DB)
- No data migration needed
- No API changes needed

### Risk Level: 🟢 LOW
- Models catching up to database (not other way around)
- No data loss risk
- No downtime needed

---

## Testing Checklist

After migration:
- [ ] Users CRUD works (auth-service)
- [ ] Files CRUD works (diagram-service)
- [ ] Versions CRUD works (diagram-service)
- [ ] Folders CRUD works (both services)
- [ ] No "column does not exist" errors in logs
- [ ] All existing features still pass

---

## Conclusion

**Schema State:** Database is AHEAD of models (low risk)
**Action Needed:** Update model files to match database
**Database Migration:** NOT NEEDED (database already correct)
**Code Changes:** Update 2 model files
**Risk:** Low - models catching up to existing schema

**Next Steps:**
1. Update auth-service/src/models.py
2. Update diagram-service/src/models.py
3. Restart services
4. Test CRUD operations
5. Mark Feature #655 as passing

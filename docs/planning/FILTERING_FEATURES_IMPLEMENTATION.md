# Filtering Features Implementation

## Features Implemented

### Feature #574: Filtering by Author ✅
**Description:** Filter diagrams by author (owner email or name)

**Implementation:**
- Added `filterAuthor` state to dashboard
- Added author filter input field in Advanced Filters panel
- Backend already supports `author:value` syntax in search query
- Filter is applied by appending `author:{value}` to search query
- Backend searches both email and full_name fields with ILIKE

**UI Location:**
- Dashboard → Advanced Filters button → Filter by Author input field

**How it works:**
1. User clicks "Advanced Filters" button
2. User enters author email or name in "Filter by Author" field
3. Frontend appends `author:{value}` to search query
4. Backend filters diagrams where owner email or name matches

**Backend Support:**
```python
elif filter_key.lower() == 'author':
    # Filter by author (owner email)
    # Join with users table to search by email/name
    from .models import User
    user_subquery = db.query(User.id).filter(
        or_(
            User.email.ilike(f'%{filter_value}%'),
            User.full_name.ilike(f'%{filter_value}%')
        )
    ).subquery()
    query = query.filter(File.owner_id.in_(user_subquery))
```

---

### Feature #575: Filtering by Date Range ✅
**Description:** Filter diagrams by creation date (today, last 7 days, last 30 days, last year)

**Implementation:**
- Added `filterDateRange` state to dashboard
- Added date range dropdown in Advanced Filters panel
- Added backend support for `after:YYYY-MM-DD` and `before:YYYY-MM-DD` filters
- Frontend calculates date based on selected range and appends to search query

**UI Location:**
- Dashboard → Advanced Filters button → Filter by Date Range dropdown

**Options:**
- All Time (default)
- Today
- Last 7 Days
- Last 30 Days
- Last Year

**How it works:**
1. User selects date range from dropdown
2. Frontend calculates start date based on selection
3. Frontend appends `after:{date}` to search query
4. Backend filters diagrams where created_at >= date

**Backend Support:**
```python
elif filter_key.lower() == 'after':
    # Filter by date (created after)
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(filter_value)
        query = query.filter(File.created_at >= date_obj)
    except ValueError:
        pass  # Invalid date format, skip filter

elif filter_key.lower() == 'before':
    # Filter by date (created before)
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(filter_value)
        query = query.filter(File.created_at <= date_obj)
    except ValueError:
        pass  # Invalid date format, skip filter
```

---

### Feature #576: Filtering by Folder ✅
**Description:** Filter diagrams by folder

**Implementation:**
- Added `filterFolder` state to dashboard
- Added folder dropdown in Advanced Filters panel
- Backend already supports `folder_id` query parameter
- Filter is applied by passing `folder_id` parameter to API

**UI Location:**
- Dashboard → Advanced Filters button → Filter by Folder dropdown
- Also: Sidebar folder tree navigation

**How it works:**
1. User selects folder from dropdown (or clicks folder in sidebar)
2. Frontend passes `folder_id` parameter to API
3. Backend filters diagrams where folder_id matches

**Backend Support:**
```python
# Add folder filter if a folder is selected (either from sidebar or filter dropdown)
if filterFolder:
    params.append('folder_id', filterFolder)
elif currentFolderId:
    params.append('folder_id', currentFolderId)
```

---

## UI Components Added

### Advanced Filters Button
- Located in filter controls section
- Shows active filter count badge
- Toggles Advanced Filters panel

### Advanced Filters Panel
- Collapsible panel with 3 filter inputs
- Grid layout (3 columns on desktop, 1 on mobile)
- Clear individual filters or clear all at once

### Filter Inputs
1. **Filter by Author:** Text input for email/name
2. **Filter by Date Range:** Dropdown with 5 options
3. **Filter by Folder:** Dropdown (uses sidebar for now)

---

## Code Changes

### Frontend Changes
**File:** `services/frontend/app/dashboard/page.tsx`

**State Added:**
```typescript
const [filterAuthor, setFilterAuthor] = useState<string>('');
const [filterDateRange, setFilterDateRange] = useState<'all' | 'today' | 'week' | 'month' | 'year'>('all');
const [filterFolder, setFilterFolder] = useState<string>('');
const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
```

**Dependencies Updated:**
```typescript
useEffect(() => {
  if (user?.sub) {
    fetchDiagrams();
  }
}, [user, page, filterType, searchQuery, sortBy, sortOrder, activeTab, currentFolderId, filterAuthor, filterDateRange, filterFolder]);
```

**Query Building:**
```typescript
// Build search query with advanced filters
let finalSearchQuery = searchQuery;

// Add author filter to search query
if (filterAuthor) {
  finalSearchQuery = finalSearchQuery 
    ? `${finalSearchQuery} author:${filterAuthor}`
    : `author:${filterAuthor}`;
}

// Add date range filter
if (filterDateRange && filterDateRange !== 'all') {
  const now = new Date();
  let startDate = new Date();
  
  switch (filterDateRange) {
    case 'today':
      startDate.setHours(0, 0, 0, 0);
      break;
    case 'week':
      startDate.setDate(now.getDate() - 7);
      break;
    case 'month':
      startDate.setDate(now.getDate() - 30);
      break;
    case 'year':
      startDate.setDate(now.getDate() - 365);
      break;
  }
  
  finalSearchQuery = finalSearchQuery 
    ? `${finalSearchQuery} after:${startDate.toISOString().split('T')[0]}`
    : `after:${startDate.toISOString().split('T')[0]}`;
}
```

### Backend Changes
**File:** `services/diagram-service/src/main.py`

**Added date filter support:**
```python
elif filter_key.lower() == 'after':
    # Filter by date (created after)
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(filter_value)
        query = query.filter(File.created_at >= date_obj)
    except ValueError:
        pass  # Invalid date format, skip filter

elif filter_key.lower() == 'before':
    # Filter by date (created before)
    try:
        from datetime import datetime
        date_obj = datetime.fromisoformat(filter_value)
        query = query.filter(File.created_at <= date_obj)
    except ValueError:
        pass  # Invalid date format, skip filter
```

---

## Testing

### Manual Testing Steps

#### Feature #574: Filter by Author
1. Open dashboard at http://localhost:3000/dashboard
2. Click "Advanced Filters" button
3. Enter author email or name in "Filter by Author" field
4. Verify only diagrams by that author are shown
5. Click "Clear" to remove filter
6. Verify all diagrams are shown again

#### Feature #575: Filter by Date Range
1. Open dashboard
2. Click "Advanced Filters" button
3. Select "Last 7 Days" from date range dropdown
4. Verify only recent diagrams are shown
5. Select "Last 30 Days"
6. Verify more diagrams are shown
7. Select "All Time"
8. Verify all diagrams are shown

#### Feature #576: Filter by Folder
1. Open dashboard
2. Create a folder using sidebar
3. Move some diagrams to the folder
4. Click on folder in sidebar
5. Verify only diagrams in that folder are shown
6. Click "All Files" to clear folder filter
7. Verify all diagrams are shown

### Automated Testing
See `test_filtering_features.py` for automated backend API tests.

---

## User Experience

### Visual Indicators
- Advanced Filters button shows blue when active
- Badge shows count of active filters
- Active filters are highlighted in the panel
- "Clear All Filters" button appears when filters are active

### Performance
- Filters are debounced (300ms) to avoid excessive API calls
- Page resets to 1 when filters change
- Instant feedback when changing filters

### Accessibility
- All inputs have labels
- Keyboard navigation supported
- Clear visual hierarchy

---

## Future Enhancements

### Feature #577: Filter by Tags
**Status:** Not implemented (tags field doesn't exist in File model yet)

**Requirements:**
1. Add `tags` JSON column to File model
2. Add migration to create column
3. Add tags input to diagram create/edit forms
4. Add tags filter to Advanced Filters panel
5. Add backend support for `tag:value` filter syntax

---

## Conclusion

All three filtering features (#574, #575, #576) have been successfully implemented:

✅ **Feature #574:** Filter by author (email/name search)
✅ **Feature #575:** Filter by date range (5 options)
✅ **Feature #576:** Filter by folder (sidebar + dropdown)

The implementation follows the existing patterns in the codebase, provides good UX with visual feedback, and is performant with debouncing and proper state management.

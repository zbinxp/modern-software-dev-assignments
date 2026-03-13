# Task 8: List Endpoint Pagination for All Collections

## Task Overview

Add pagination to `GET /notes` and `GET /action-items` endpoints, returning `items` and `total` for each. Update the frontend to paginate lists and add tests for boundary cases (empty last page, too-large page size).

---

## Current State Analysis

### Backend

1. **GET /notes/** (`/backend/app/routers/notes.py` line 124-128):
   - Currently returns all notes as `SuccessResponse[list[NoteReadWithTags]]`
   - No pagination parameters
   - Search endpoint (`/notes/search/`) already has full pagination

2. **GET /action-items/** (`/backend/app/routers/action_items.py` line 24-34):
   - Currently returns all items as `SuccessResponse[list[ActionItemRead]]`
   - Has `completed` filter parameter
   - No pagination parameters

### Frontend

1. **NotesList.jsx**:
   - Uses `searchNotes()` which already has pagination (page, page_size, sort)
   - Shows pagination controls
   - The `getNotes()` function is defined but not used in the component

2. **ActionItemsList.jsx**:
   - Uses `getActionItems(filter)` which returns a flat array
   - No pagination controls
   - Uses filter by `completed` status

---

## Implementation Plan

### Phase 1: Backend Changes

#### 1.1 Create Pagination Response Schema

**File:** `/backend/app/schemas.py`

Add new schemas for paginated list responses:

```python
class PaginatedNoteResponse(BaseModel):
    items: list[NoteReadWithTags]
    total: int
    page: int
    page_size: int

class PaginatedActionItemResponse(BaseModel):
    items: list[ActionItemRead]
    total: int
    page: int
    page_size: int
```

#### 1.2 Update GET /notes/ Endpoint

**File:** `/backend/app/routers/notes.py`

Modify `list_notes` function:
- Add query parameters: `page: int = 1`, `page_size: int = 10`
- Cap `page_size` at 100
- Ensure `page` is at least 1
- Add count query using `func.count()`
- Apply offset and limit to query
- Return paginated response with `items` and `total`

#### 1.3 Update GET /action-items/ Endpoint

**File:** `/backend/app/routers/action_items.py`

Modify `list_items` function:
- Add query parameters: `page: int = 1`, `page_size: int = 10`
- Cap `page_size` at 100
- Ensure `page` is at least 1
- Add count query with filter applied
- Apply offset and limit
- Return paginated response with `items` and `total`

---

### Phase 2: Frontend Changes

#### 2.1 Update API Functions

**File:** `/frontend/src/api.js`

Update `getNotes` and `getActionItems` to support pagination:

```javascript
export async function getNotes(page = 1, pageSize = 10) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  return fetchJSON(`/notes/?${params.toString()}`);
}

export async function getActionItems(completed = null, page = 1, pageSize = 10) {
  const params = new URLSearchParams();
  if (completed !== null) params.append('completed', completed);
  params.append('page', page);
  params.append('page_size', pageSize);
  return fetchJSON(`/action-items/?${params.toString()}`);
}
```

#### 2.2 Update NotesList Component

**File:** `/frontend/src/components/NotesList.jsx`

The NotesList already has pagination UI via searchNotes. For this task:
- Update to optionally use paginated `getNotes()` endpoint for non-search views
- Ensure pagination controls work with the new response format

#### 2.3 Update ActionItemsList Component

**File:** `/frontend/src/components/ActionItemsList.jsx`

Add pagination:
- Add state: `currentPage`, `pageSize`, `totalItems`
- Update `fetchItems` to accept pagination params
- Add pagination controls (Previous/Next buttons, page indicator)
- Handle edge cases

---

### Phase 3: Backend Tests

#### 3.1 Tests for GET /notes/ Pagination

**File:** `/backend/tests/test_notes.py`

Add tests:
- `test_list_notes_pagination_returns_correct_subset` - verify correct items returned per page
- `test_list_notes_pagination_empty_last_page` - verify empty last page handling
- `test_list_notes_pagination_large_page_size` - verify large page size returns all
- `test_list_notes_invalid_page_defaults_to_1` - verify invalid page defaults
- `test_list_notes_page_size_capped_at_100` - verify page size cap

#### 3.2 Tests for GET /action-items/ Pagination

**File:** `/backend/tests/test_action_items.py`

Add tests:
- `test_list_action_items_pagination_returns_correct_subset`
- `test_list_action_items_pagination_empty_last_page`
- `test_list_action_items_pagination_with_filter` - verify pagination with completed filter

---

### Phase 4: Frontend Tests

**Files:** `/frontend/src/__tests__/NotesList.test.jsx` and `/frontend/src/__tests__/ActionItemsList.test.jsx`

Add tests for:
- Pagination controls render when there are multiple pages
- Previous/Next buttons work correctly
- Empty last page handling
- Large page size handled correctly

---

## Files to Modify

### Backend
1. `/backend/app/schemas.py` - Add paginated response schemas
2. `/backend/app/routers/notes.py` - Add pagination to list_notes endpoint
3. `/backend/app/routers/action_items.py` - Add pagination to list_items endpoint
4. `/backend/tests/test_notes.py` - Add pagination tests
5. `/backend/tests/test_action_items.py` - Add pagination tests

### Frontend
1. `/frontend/src/api.js` - Update getNotes and getActionItems for pagination
2. `/frontend/src/components/NotesList.jsx` - Update to use paginated getNotes
3. `/frontend/src/components/ActionItemsList.jsx` - Add pagination UI

---

## Edge Cases to Handle

1. **Empty database**: Return empty items array with total=0
2. **Page beyond available**: Return empty items array but preserve total count
3. **Invalid page (0 or negative)**: Default to page 1
4. **Large page size**: Cap at 100
5. **Exact page size match**: Show next page available
6. **Single page of results**: Should not show pagination controls

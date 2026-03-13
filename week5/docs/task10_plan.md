# Task 10: Test Coverage Improvements Plan

## Overview

This plan outlines the test coverage improvements needed for the FastAPI + React application. The goal is to add comprehensive tests covering error scenarios (400/404), concurrency/transactional behavior for bulk operations, and frontend integration tests for search, pagination, and optimistic updates.

## Current Test Coverage Analysis

### Backend Tests (Existing)
- **test_notes.py**: CRUD operations, search, pagination, sorting, validation errors, tag operations
- **test_action_items.py**: CRUD operations, filtering, bulk complete, transaction rollback
- **test_tags.py**: CRUD operations, duplicate handling

### Frontend Tests (Existing)
- **NotesList.test.jsx**: Loading, empty state, error, create, delete, pagination controls
- **ActionItemsList.test.jsx**: Loading, empty state, error, create, complete, delete, bulk complete, filters

---

## Test Files to Modify/Create

### Backend Tests (Modify existing)
1. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_notes.py` - Add error scenarios
2. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_action_items.py` - Add error scenarios  
3. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_tags.py` - Add validation tests

### Frontend Tests (Modify existing)
1. `/home/dd/lab/modern-software-dev-assignments/week5/frontend/src/__tests__/NotesList.test.jsx` - Add search, pagination, optimistic update tests
2. `/home/dd/lab/modern-software-dev-assignments/week5/frontend/src/__tests__/ActionItemsList.test.jsx` - Add optimistic update tests

---

## Test Cases: 400/404 Scenarios

### Notes Endpoints

| Endpoint | Test Case | Expected Status | Test Name |
|----------|-----------|-----------------|-----------|
| POST /notes/{note_id}/extract | Non-existent note_id | 404 | test_extract_from_nonexistent_note |
| POST /notes/{note_id}/tags | Non-existent note_id | 404 | test_attach_tags_to_nonexistent_note |
| DELETE /notes/{note_id}/tags/{tag_id} | Non-existent note_id | 404 | test_detach_tag_from_nonexistent_note |
| DELETE /notes/{note_id}/tags/{tag_id} | Non-existent tag_id | 404 | test_detach_nonexistent_tag_from_note |
| GET /notes/{note_id} | Non-existent note_id | 404 | test_get_nonexistent_note_already_covered |
| PUT /notes/{note_id} | Non-existent note_id | 404 | test_update_nonexistent_note_already_covered |
| DELETE /notes/{note_id} | Non-existent note_id | 404 | test_delete_nonexistent_note_already_covered |

### Action Items Endpoints

| Endpoint | Test Case | Expected Status | Test Name |
|----------|-----------|-----------------|-----------|
| PUT /action-items/{item_id}/complete | Non-existent item_id | 404 | test_complete_nonexistent_item_covered |
| DELETE /action-items/{item_id} | Non-existent item_id | 404 | test_delete_nonexistent_action_item |
| POST /action-items/bulk-complete | Mix of valid and invalid IDs | 404 | test_bulk_complete_partial_invalid_ids |
| POST /action-items/bulk-complete | Empty ids list | 400 | test_bulk_complete_empty_ids |
| POST /action-items/ | Missing description field | 422 | test_create_action_item_missing_field |

### Tags Endpoints

| Endpoint | Test Case | Expected Status | Test Name |
|----------|-----------|-----------------|-----------|
| POST /tags/ | Empty name | 422 | test_create_tag_empty_name |
| POST /tags/ | Whitespace only | 400 | test_create_tag_whitespace_only |
| POST /tags/ | Name with special characters | 400 | test_create_tag_special_characters |

---

## Test Cases: Concurrency/Transactional Behavior

### Backend Tests (test_action_items.py)

1. **test_bulk_complete_transaction_rollback_on_partial_failure**
   - Create 3 items
   - Attempt to complete 2 valid IDs + 1 invalid ID
   - Verify 500 error returned (handled by NotFoundException before commit)
   - Verify NO items are marked complete (transaction rolled back)

2. **test_bulk_complete_empty_list_returns_success**
   - Send empty ids list to bulk-complete
   - Verify returns 200 with empty data array (edge case handling)

### Notes Bulk Tag Operations (new test file or test_notes.py)

3. **test_bulk_tag_attach_transaction_behavior**
   - Create note and multiple tags
   - Attach tags to note in single request
   - Verify all attached atomically

---

## Frontend Integration Tests

### NotesList.test.jsx - Search Tests

1. **test_search_submits_query_to_api**
   - Render component with mocked searchNotes
   - Type in search input
   - Click search button
   - Verify searchNotes called with correct parameters

2. **test_search_displays_no_results_message**
   - Mock searchNotes to return empty results
   - Render component
   - Verify "No notes found" displayed

3. **test_search_results_show_correct_count**
   - Mock searchNotes to return 5 items, total 25
   - Render component  
   - Verify "Showing 5 of 25 notes"

### NotesList.test.jsx - Pagination Tests (extend existing)

4. **test_pagination_next_button_loads_next_page**
   - Mock searchNotes to track page parameter
   - Click Next button
   - Verify searchNotes called with page=2

5. **test_pagination_previous_button_loads_previous_page**
   - Mock searchNotes to track page parameter
   - Click Previous button
   - Verify searchNotes called with page decremented

### NotesList.test.jsx - Optimistic Update Tests

6. **test_delete_note_optimistic_update**
   - Render with note displayed
   - Mock deleteNote to reject with error after delay
   - Click delete button
   - Verify note disappears immediately from UI
   - Verify error message shown after API failure

7. **test_edit_note_optimistic_update**
   - Render with note displayed
   - Click Edit button
   - Modify title/content
   - Click Save
   - Verify note updates immediately in UI
   - Mock updateNote to reject
   - Verify original content restored after API failure

### ActionItemsList.test.jsx - Optimistic Update Tests

8. **test_complete_item_optimistic_update**
   - Render with incomplete item
   - Mock completeActionItem to reject
   - Click Complete button
   - Verify item still shows as incomplete (or shows error)
   - Test rollback behavior

---

## Implementation Priority

### Phase 1: Backend Error Scenarios (Easy)
- Add 400/404 tests to existing test files
- Focus on missing error cases identified above

### Phase 2: Backend Transactional Tests (Medium)
- Enhance bulk operation tests
- Add partial failure scenarios

### Phase 3: Frontend Integration Tests (Medium)
- Add search integration tests
- Add pagination interaction tests  
- Add optimistic update rollback tests

---

## Testing Patterns to Use

### Backend Patterns
- Use existing `client` fixture from conftest.py
- Follow naming convention: `test_<endpoint>_<scenario>`
- Assert both status code and error envelope format
- Use `@pytest.fixture` for reusable test data

### Frontend Patterns
- Continue using existing vi.mock() pattern for API
- Use fireEvent for user interactions
- Use waitFor for async state updates
- Test both success and failure paths for optimistic updates

---

## Files to Modify

1. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_notes.py` - Add ~10 new test cases
2. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_action_items.py` - Add ~5 new test cases
3. `/home/dd/lab/modern-software-dev-assignments/week5/backend/tests/test_tags.py` - Add ~3 new test cases
4. `/home/dd/lab/modern-software-dev-assignments/week5/frontend/src/__tests__/NotesList.test.jsx` - Add ~7 new test cases
5. `/home/dd/lab/modern-software-dev-assignments/week5/frontend/src/__tests__/ActionItemsList.test.jsx` - Add ~1 new test case

---

## Success Criteria

- [ ] All 400/404 error scenarios covered for each endpoint
- [ ] Bulk operation transactional behavior verified
- [ ] Frontend search functionality tested with API integration
- [ ] Frontend pagination controls tested with API calls
- [ ] Optimistic update rollbacks tested for both success and failure paths
- [ ] All tests pass: `make test` and `make web-test`

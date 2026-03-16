# Task Plan: Add CRUD Support to Notes

## Context

The notes feature currently has partial CRUD functionality. The backend has Create, Read, and Update (PATCH) endpoints but lacks Delete. The frontend only supports creating and listing notes, with no edit or delete UI. Input validation is minimal (just required fields), and test coverage is incomplete.

**Goal**: Complete the notes CRUD implementation with proper validation, error handling, frontend UI, and unit tests.

---

## Current State Analysis

### Backend (`backend/app/routers/notes.py`)
| Endpoint | Method | Status |
|----------|--------|--------|
| `/notes/` | GET | ✅ List with search/sort/pagination |
| `/notes/` | POST | ✅ Create |
| `/notes/{id}` | GET | ✅ Get single |
| `/notes/{id}` | PATCH | ✅ Update |
| `/notes/{id}` | DELETE | ❌ Missing |

### Backend Validation (`backend/app/schemas.py`)
- `NoteCreate`: basic `str` types, no length limits
- `NotePatch`: optional fields, no validation
- No min/max length constraints
- No empty string validation

### Frontend (`frontend/app.js`, `index.html`)
- Create form ✅
- List display ✅
- Search ✅
- Edit UI ❌
- Delete UI ❌
- Validation feedback ❌

### Tests (`backend/tests/test_notes.py`)
- Create/List/Patch ✅
- Delete ❌
- Validation errors (400) ❌
- Edge cases ❌

---

## Implementation Plan

### Phase 1: Backend - Input Validation & Delete

**File: `backend/app/schemas.py`**
- Add Pydantic validation to `NoteCreate`:
  - `title`: `str` with `min_length=1`, `max_length=200`
  - `content`: `str` with `min_length=1`
- Add same validation to `NotePatch`

**File: `backend/app/routers/notes.py`**
- Add DELETE endpoint: `@router.delete("/{note_id}", status_code=204)`
- Return 404 if note not found
- Add proper error handling for validation errors (422)

### Phase 2: Frontend - Edit & Delete UI

**File: `frontend/index.html`**
- Add edit/delete buttons to each note in the list
- Add a hidden edit form or modal for editing

**File: `frontend/app.js`**
- Update `loadNotes()` to include edit/delete buttons
- Add `editNote(noteId)` function
- Add `deleteNote(noteId)` function
- Add error handling with user feedback

### Phase 3: Unit Tests

**File: `backend/tests/test_notes.py`**
- Add test for DELETE endpoint (204, 404)
- Add test for validation errors (422):
  - Empty title
  - Empty content
  - Title too long (>200 chars)
- Add test for 404 on non-existent note

---

## Critical Files

| File | Changes |
|------|---------|
| `backend/app/schemas.py` | Add Pydantic validation constraints |
| `backend/app/routers/notes.py` | Add DELETE endpoint |
| `frontend/index.html` | Add edit/delete buttons |
| `frontend/app.js` | Add edit/delete handlers |
| `backend/tests/test_notes.py` | Add comprehensive tests |

---

## Verification

1. **Backend Tests**: Run `make test` to verify all tests pass
2. **Manual Testing**:
   - Create a note via UI
   - Edit a note via UI
   - Delete a note via UI
   - Test validation: submit empty title/content
3. **API Testing**:
   - `DELETE /notes/1` returns 204
   - `DELETE /notes/999` returns 404
   - `POST /notes/` with empty title returns 422

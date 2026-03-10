# Week4 Project Notes

## Project Overview
- FastAPI backend with SQLite database
- Notes and Action Items management API
- Uses SQLAlchemy ORM with dependency injection for database sessions

## Running Tests
change to week4 directory
```bash
PYTHONPATH=. poetry run pytest -q backend/tests
```

## Running Coverage
change to week4 directory
```bash
PYTHONPATH=. poetry run coverage run -m pytest -q backend/tests
```

## Test Coverage (86%)
- Low coverage areas:
  - `backend/app/db.py` - 49% (database helper functions)
  - `backend/app/routers/notes.py` - 87%

## Known Issues
- Pydantic v2 deprecation warnings for class-based `config` (should use `ConfigDict`)
- FastAPI `on_event` deprecation (should use lifespan handlers)
- Frontend directory not present (tests import from `backend.app.main`)

## Key Files
- `backend/app/main.py` - FastAPI app entry point
- `backend/app/db.py` - Database session management
- `backend/app/models.py` - SQLAlchemy models
- `backend/app/schemas.py` - Pydantic schemas
- `backend/app/routers/` - API route handlers
- `backend/tests/conftest.py` - Test fixtures with in-memory SQLite

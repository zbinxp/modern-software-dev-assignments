# Project Overview

Full-stack FastAPI + React application with SQLite database.

## Key Technologies

- **Backend**: FastAPI, SQLAlchemy, pytest
- **Frontend**: React 18, Vite, Vitest, React Testing Library
- **Database**: SQLite

## Make Targets

| Target | Description |
|--------|-------------|
| `make run` | Build frontend and start uvicorn dev server |
| `make test` | Run backend pytest tests |
| `make web-install` | Install frontend npm dependencies |
| `make web-dev` | Run Vite dev server |
| `make web-build` | Build frontend for production |
| `make web-test` | Run frontend Vitest tests |
| `make seed` | Seed database with sample data |

## Recent Changes

- Migrated from vanilla JavaScript to React 18
- Fixed trailing slash redirect issues on API routes
- Added tags table with full backend/frontend support

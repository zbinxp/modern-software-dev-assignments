.PHONY: run test format lint seed web-install web-dev web-build web-test

web-install:
	cd frontend && npm install

web-dev:
	cd frontend && npm run dev

web-build:
	cd frontend && npm run build

web-test:
	cd frontend && npm test

run: web-build
	PYTHONPATH=. poetry run uvicorn backend.app.main:app --reload --host $${HOST:-127.0.0.1} --port $${PORT:-8000}

test: web-build
	PYTHONPATH=. poetry run pytest -q backend/tests

format:
	black .
	ruff check . --fix

lint:
	ruff check .

seed:
	PYTHONPATH=. poetry run python -c "from backend.app.db import apply_seed_if_needed; apply_seed_if_needed()"

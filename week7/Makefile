.PHONY: run test format lint seed

run:
	PYTHONPATH=. poetry run uvicorn backend.app.main:app --reload --host $${HOST:-127.0.0.1} --port $${PORT:-8000}

test:
	PYTHONPATH=. poetry run pytest -q backend/tests

format:
	black .
	ruff check . --fix

lint:
	ruff check .

seed:
	PYTHONPATH=. poetry run python -c "from backend.app.db import apply_seed_if_needed; apply_seed_if_needed()"



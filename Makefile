.PHONY: backend-install backend-run backend-test backend-lint frontend-install frontend-dev frontend-lint frontend-test format docker-build docker-up docker-down

backend-install:
	python -m pip install -r backend/requirements.txt

backend-run:
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

backend-test:
	pytest backend/tests -q

backend-lint:
	ruff check backend

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm test

format:
	cd frontend && npm run format

docker-build:
	docker compose build

docker-up:
	docker compose up

docker-down:
	docker compose down
